import { useSignal } from '@preact/signals-react';
import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

/** Props for the generic TanStack Table v8 wrapper. */
interface DataTableProps<TData, TValue> {
  /** Strongly typed column definitions for the table. */
  columns: ColumnDef<TData, TValue>[];
  /** Row data array to display. */
  data: TData[];
  /** Optional column ID to bind the search filter input to. */
  searchColumn?: string;
  /** Placeholder text for the search input. */
  searchPlaceholder?: string;
  /** Number of rows per page (defaults to `15`). */
  pageSize?: number;
}

/**
 * Reusable TanStack Table v8 component with sorting, column filtering, and pagination.
 */
export function DataTable<TData, TValue>({
  columns,
  data,
  searchColumn,
  searchPlaceholder = 'Filter...',
  pageSize = 15,
}: DataTableProps<TData, TValue>) {
  const sorting = useSignal<SortingState>([]);
  const columnFilters = useSignal<ColumnFiltersState>([]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: updater => {
      sorting.value = typeof updater === 'function' ? updater(sorting.value) : updater;
    },
    onColumnFiltersChange: updater => {
      columnFilters.value =
        typeof updater === 'function' ? updater(columnFilters.value) : updater;
    },
    initialState: { pagination: { pageSize } },
    state: { sorting: sorting.value, columnFilters: columnFilters.value },
  });

  return (
    <div className="space-y-3">
      {searchColumn && (
        <div className="flex items-center justify-between gap-3">
          <Input
            placeholder={searchPlaceholder}
            value={(table.getColumn(searchColumn)?.getFilterValue() as string) ?? ''}
            onChange={event => table.getColumn(searchColumn)?.setFilterValue(event.target.value)}
            className="max-w-xs"
          />
          <span className="font-mono text-[11px] text-zinc-500">
            {table.getFilteredRowModel().rows.length} rows
          </span>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
        <Table>
          <TableHeader className="bg-zinc-50/70">
            {table.getHeaderGroups().map(headerGroup => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <TableHead key={header.id} className="text-[11px] font-medium text-zinc-500">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map(row => (
                <TableRow key={row.id} className="hover:bg-emerald-50/30">
                  {row.getVisibleCells().map(cell => (
                    <TableCell key={cell.id} className="text-xs">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-zinc-400">
                  No matching records.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between text-xs text-zinc-500">
        <span className="font-mono text-[11px]">
          Page {table.getState().pagination.pageIndex + 1} of {Math.max(table.getPageCount(), 1)}
        </span>
        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Prev
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
