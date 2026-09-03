# Data Engineering Case Study

This context defines the language used to design and maintain the take-home exercise for Data Operations Engineer candidates.

## Language

**Baseline Application**:
The fully working, tested application before the four Requested Changes are implemented or any Seeded Defects are introduced.
_Avoid_: Starter app, clean version

**Reference Application**:
The private, fully working implementation of all four Requested Changes, used to document and verify expected behavior.
_Avoid_: Answer repository, solution branch

**Candidate Exercise**:
The repository distributed to a candidate, derived from the Baseline Application and containing six Seeded Defects. Its Git history does not expose the Reference Application or private materials.
_Avoid_: Broken app, test repository

**Requested Change**:
One of four candidate-facing changes to the application's behavior. Completing these changes is the stated assignment.
_Avoid_: Task, bug

**Seeded Defect**:
One of six deliberate faults placed in the Candidate Exercise to provide realistic diagnosis and repair work while completing Requested Changes.
_Avoid_: Trick, hidden task, incidental bug

**Snapshot**:
A dated profile CSV representing the vendor's complete view of professional-profile data at that point in time. Each source profile has a stable `profile_id`.
_Avoid_: Export, batch

**Profile Version**:
A period-bounded historical representation of a profile's company, job title, and department, with exactly one current version per active profile and none per inactive profile. Display-name changes do not create a new version.
_Avoid_: Employee record, history row

**Interviewer Guide**:
Private explanatory material that helps an interviewer understand the application, expected changes, Seeded Defects, and productive candidate follow-up questions. It is not a scoring rubric.
_Avoid_: Scorecard, answer key
