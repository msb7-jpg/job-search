# Delta Specification: Recruiter Outreach

## ADDED Requirements

### Requirement: Recruiter Association and Connection Tracking
Each job/application MUST support storing a recruiter's LinkedIn profile URL and tracking whether the user has connected with them.

#### Scenario: Recording recruiter and connection status
- **WHEN** the user saves a recruiter LinkedIn URL on a job and toggles connection status
- **THEN** the state persists in SQLite and is reflected in the UI

### Requirement: Tailored Recruiter DM Generation
The system MUST generate a concise, tailored outreach DM using the job description and `MasterProfile` without inventing experience.

#### Scenario: Generating a tailored DM
- **WHEN** the user requests a recruiter DM for a job
- **THEN** the backend calls the configured OpenAI-compatible LLM and returns an editable draft DM aligned with the role
