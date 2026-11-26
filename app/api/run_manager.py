import logging
import queue
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import logger as app_logger
from app.db import save_latest_scrape_run_logs


class _QueueLogHandler(logging.Handler):
    """Encaminha registros do logger para filas de streaming SSE durante execuções em background."""

    def __init__(self, target_queue: queue.Queue[str | None]) -> None:
        super().__init__()
        self.target_queue = target_queue
        self.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.target_queue.put_nowait(msg)
        except Exception:
            pass


@dataclass
class ActiveRunState:
    run_id: str
    kind: str
    status: str = "RUNNING"
    logs: list[str] = field(default_factory=list)
    subscribers: list[queue.Queue[str | None]] = field(default_factory=list)


class BackgroundRunManager:
    """Gerencia execuções em background (scrape / rejudge) com lock único e streaming SSE."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_run_id: str | None = None
        self._runs: dict[str, ActiveRunState] = {}

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._active_run_id is not None

    @property
    def active_run_id(self) -> str | None:
        with self._lock:
            return self._active_run_id

    def start_run(
        self,
        kind: str,
        target_fn: Callable[[], object],
        db_path: Path | None = None,
    ) -> str | None:
        """Inicia uma tarefa em thread separada. Retorna run_id ou None se já houver execução ativa."""
        with self._lock:
            if self._active_run_id is not None:
                return None
            run_id = uuid.uuid4().hex[:12]
            state = ActiveRunState(run_id=run_id, kind=kind)
            self._runs[run_id] = state
            self._active_run_id = run_id

        thread = threading.Thread(
            target=self._execute,
            args=(run_id, target_fn, db_path),
            daemon=True,
            name=f"bg-{kind}-{run_id}",
        )
        thread.start()
        return run_id

    def _execute(self, run_id: str, target_fn: Callable[[], object], db_path: Path | None) -> None:
        proxy_logger = logging.getLogger("proxy_pool")
        log_queue: queue.Queue[str | None] = queue.Queue()
        handler = _QueueLogHandler(log_queue)
        app_logger.addHandler(handler)
        proxy_logger.addHandler(handler)

        stop_pump = threading.Event()

        def _pump_logs() -> None:
            while not stop_pump.is_set() or not log_queue.empty():
                try:
                    line = log_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if line is None:
                    break
                with self._lock:
                    state = self._runs[run_id]
                    state.logs.append(line)
                    for sub in state.subscribers:
                        sub.put_nowait(line)

        pump_thread = threading.Thread(target=_pump_logs, daemon=True)
        pump_thread.start()

        final_status = "COMPLETED"
        try:
            target_fn()
        except Exception:
            final_status = "FAILED"
            app_logger.exception(f"❌ Falha na execução em background ({run_id})")
        finally:
            stop_pump.set()
            log_queue.put_nowait(None)
            pump_thread.join(timeout=2.0)
            app_logger.removeHandler(handler)
            proxy_logger.removeHandler(handler)

            with self._lock:
                state = self._runs[run_id]
                state.status = final_status
                logs_snapshot = "\n".join(state.logs)
                for sub in state.subscribers:
                    sub.put_nowait(None)
                if self._active_run_id == run_id:
                    self._active_run_id = None

            if db_path is not None and state.kind == "scrape" and logs_snapshot:
                try:
                    save_latest_scrape_run_logs(db_path, logs_snapshot)
                except Exception:
                    app_logger.exception(f"Falha ao persistir logs do scrape ({run_id})")

    def subscribe(self, run_id: str) -> tuple[list[str], queue.Queue[str | None], bool] | None:
        """Retorna (logs_existentes, fila_live, ja_finalizado) ou None se run_id não existir."""
        with self._lock:
            state = self._runs.get(run_id)
            if state is None:
                return None
            live_queue: queue.Queue[str | None] = queue.Queue()
            snapshot = list(state.logs)
            finished = state.status != "RUNNING"
            if not finished:
                state.subscribers.append(live_queue)
            return snapshot, live_queue, finished


run_manager = BackgroundRunManager()
