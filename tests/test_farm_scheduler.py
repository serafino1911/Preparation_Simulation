import unittest

from windows.farm_scheduler import build_submission_command


class BuildSubmissionCommandTests(unittest.TestCase):
    def test_slurm_submission_targets_configured_node(self):
        command = build_submission_command(
            "slurm", "run.sh", "job.out", "job.err", node="compute-01"
        )

        self.assertIn("-w compute-01", command)

    def test_slurm_submission_omits_empty_node(self):
        command = build_submission_command(
            "slurm", "run.sh", "job.out", "job.err", node="  "
        )

        self.assertNotIn("-w", command)

    def test_lsf_submission_ignores_slurm_node(self):
        command = build_submission_command(
            "lsf - bjobs", "run.sh", "job.out", "job.err", node="compute-01"
        )

        self.assertTrue(command.startswith("bsub "))
        self.assertNotIn("-w", command)


if __name__ == "__main__":
    unittest.main()
