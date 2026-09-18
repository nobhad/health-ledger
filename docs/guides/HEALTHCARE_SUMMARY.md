# Healthcare Summary Guide

This guide explains how to add and manage healthcare summaries after doctor's appointments.

## Quick Start

### Adding a Healthcare Summary After an Appointment

Run the interactive script:

```bash
python3 scripts/add_healthcare_summary.py
```

The script will prompt you for:
- Visit date
- Doctor/Provider name
- Institution/Clinic
- Visit type (sick visit, routine visit, etc.)
- Chief complaint
- Symptoms
- Diagnosis
- Treatment/Plan
- Medications
- Follow-up instructions
- Additional notes

### Quick Add (Command Line)

For quick additions without prompts:

```bash
python3 scripts/add_healthcare_summary.py --quick "2025-01-15" "Dr. Smith" "Headache and fatigue" "Migraine"
```

### Viewing Healthcare Summaries

View all summaries:
```bash
python3 scripts/view_healthcare_summaries.py
```

View only sick visits:
```bash
python3 scripts/view_healthcare_summaries.py --sick
```

View only routine visits:
```bash
python3 scripts/view_healthcare_summaries.py --routine
```

View recent summaries (last 5):
```bash
python3 scripts/view_healthcare_summaries.py --limit 5
```

View by date range:
```bash
python3 scripts/view_healthcare_summaries.py --start "2024-01-01" --end "2024-12-31"
```

## Visit Types

The system categorizes visits as:
- **sick_visit**: Illness, symptoms, acute issues
- **routine_visit**: Checkups, follow-ups, preventive care
- **emergency_visit**: Emergency room visits
- **specialist_consultation**: Specialist appointments
- **other_visit**: Other types of visits

## Cross-Referencing

The system automatically cross-references healthcare summaries with:
- Lab results from the same time period
- Test results and imaging
- Other medical records

This helps determine if a health log entry was for a sick visit by checking if there were abnormal lab results or tests around the same date.

## Database Structure

Healthcare summaries are stored in:
- **primary_sources** table: Main summary information
- **primary_source_findings** table: Individual findings (symptoms, diagnoses, treatments, etc.)

Each summary can have multiple findings, making it easy to track:
- Symptoms
- Diagnoses
- Treatments
- Medications
- Follow-up instructions

## Workflow

1. **After each appointment**: Run `add_healthcare_summary.py` to add the visit details
2. **When you receive lab/test results**: The system can cross-reference them with your visits
3. **Review your history**: Use `view_healthcare_summaries.py` to see your medical history

## Integration with Other Documents

The system can automatically:
- Link lab results to visits
- Cross-reference test results with symptoms
- Track medication changes over time
- Identify patterns in your healthcare

## Example Workflow

```bash
# After a doctor's appointment
python3 scripts/add_healthcare_summary.py

# Later, when you get lab results
# (The system will automatically cross-reference if dates match)

# View your recent visits
python3 scripts/view_healthcare_summaries.py --limit 10

# Check all sick visits this year
python3 scripts/view_healthcare_summaries.py --sick --start "2025-01-01"
```

## Tips

1. **Be consistent**: Add summaries soon after appointments while details are fresh
2. **Include all details**: The more information you add, the better the cross-referencing works
3. **Link documents**: When prompted, provide paths to lab/test result files for automatic linking
4. **Review regularly**: Use the view script to review your medical history and identify patterns

