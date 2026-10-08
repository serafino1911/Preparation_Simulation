"""Helpers for building remote LSF and Slurm commands."""

import re
import shlex


LSF_SCHEDULER = "lsf - bjobs"
SLURM_SCHEDULER = "slurm"

SLURM_SUCCESS_STATES = {"COMPLETED"}
SLURM_FAILURE_STATES = {
    "BOOT_FAIL",
    "CANCELLED",
    "DEADLINE",
    "FAILED",
    "NODE_FAIL",
    "OUT_OF_MEMORY",
    "PREEMPTED",
    "REVOKED",
    "TIMEOUT",
}
SLURM_RUNNING_STATES = {
    "COMPLETING",
    "CONFIGURING",
    "PENDING",
    "REQUEUED",
    "REQUEUE_FED",
    "REQUEUE_HOLD",
    "RESIZING",
    "RUNNING",
    "SIGNALING",
    "SUSPENDED",
    "WAITING",
}


def normalize_scheduler(scheduler):
    """Use Slurm only for an explicit Slurm selection; preserve legacy LSF defaults."""
    return SLURM_SCHEDULER if str(scheduler or "").strip().lower() == SLURM_SCHEDULER else LSF_SCHEDULER


def build_submission_command(
    scheduler,
    command,
    output_path,
    error_path,
    partition="",
    queue="pmten",
    working_directory=None,
    wrap_command=False,
):
    """Build an LSF or Slurm submission command for a script or shell command."""
    scheduler = normalize_scheduler(scheduler)
    if scheduler == SLURM_SCHEDULER:
        options = ["sbatch", "--parsable"]
        if partition:
            options.append(f"--partition={shlex.quote(str(partition))}")
        options.extend((
            f"--output={shlex.quote(str(output_path))}",
            f"--error={shlex.quote(str(error_path))}",
        ))
        if wrap_command:
            options.extend(("--wrap", shlex.quote(command)))
        else:
            options.append(shlex.quote(command))
    else:
        options = [
            "bsub",
            "-q", shlex.quote(queue),
            "-o", shlex.quote(str(output_path)),
            "-e", shlex.quote(str(error_path)),
            f"/bin/bash -lc {shlex.quote(command)}" if wrap_command else shlex.quote(command),
        ]

    submission = " ".join(options)
    if working_directory:
        return f"cd {shlex.quote(str(working_directory))} && {submission}"
    return submission


def build_check_jobs_command(scheduler):
    """Build the command used to list jobs for the connected user."""
    if normalize_scheduler(scheduler) == SLURM_SCHEDULER:
        return 'squeue -u "$USER"'
    return "bjobs -w"


def build_job_status_command(scheduler, job_id):
    """Build a shell command that prints one normalized job status or UNKNOWN."""
    scheduler = normalize_scheduler(scheduler)
    if scheduler == SLURM_SCHEDULER:
        return (
            f'status=$(squeue --noheader --jobs {job_id} --format=%T 2>/dev/null | head -n 1 | tr -d "[:space:] "); '
            'if [ -n "$status" ]; then echo "$status"; '
            'elif ! command -v sacct >/dev/null 2>&1; then echo "ACCOUNTING_UNAVAILABLE"; '
            'else status=$(sacct --noheader --parsable2 --allocations --jobs '
            f'{job_id} --format=State 2>/dev/null | head -n 1 | cut -d"|" -f1 | '
            'sed "s/+.*//" | tr -d "[:space:]"); '
            'if [ -n "$status" ]; then echo "$status"; else echo "UNKNOWN"; fi; fi'
        )
    return (
        f'status=$(bjobs -a -noheader -o stat {job_id} 2>/dev/null | head -n 1 | tr -d "[:space:] "); '
        'if [ -n "$status" ]; then echo "$status"; else echo "UNKNOWN"; fi'
    )


def extract_job_id(scheduler, output):
    """Extract a scheduler job ID from its submission output."""
    output = output or ""
    if normalize_scheduler(scheduler) == SLURM_SCHEDULER:
        match = re.search(r"(?:^|\s)(\d+)(?:;[^\s]+)?\s*$", output)
        if match:
            return match.group(1)
        match = re.search(r"Submitted batch job\s+(\d+)", output)
        return match.group(1) if match else None

    match = re.search(r"<([0-9]+)>", output)
    return match.group(1) if match else None


def classify_job_status(scheduler, status):
    """Return success, failure, running, or unknown for a scheduler status."""
    status = (status or "").strip().upper().split()[0] if status else ""
    if normalize_scheduler(scheduler) == SLURM_SCHEDULER:
        if status in SLURM_SUCCESS_STATES:
            return "success"
        if status in SLURM_FAILURE_STATES:
            return "failure"
        if status in SLURM_RUNNING_STATES:
            return "running"
        return "unknown"

    if status == "DONE":
        return "success"
    if status == "EXIT":
        return "failure"
    if status in {"PEND", "RUN", "PSUSP", "USUSP", "SSUSP", "UNKWN", "WAIT", "PROV"}:
        return "running"
    return "unknown"