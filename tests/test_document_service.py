import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from services.document_service import DocumentService


class DocumentServiceTests(unittest.TestCase):
    def test_successful_conversion_is_reported(self):
        service = DocumentService()
        results = []
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK", stderr=""
        )

        with patch(
            "services.document_service.subprocess.run",
            return_value=completed
        ) as run:
            service._run(
                [(Path("C:/docs/a.docx"), Path("C:/docs/a.pdf"))],
                lambda success, error: results.append((success, error))
            )

        self.assertEqual(results, [(True, "")])
        payload = run.call_args.kwargs["input"]
        self.assertIn("a.docx", payload)

    def test_failed_conversion_returns_error_text(self):
        service = DocumentService()
        results = []
        completed = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="ERROR: Word недоступен", stderr=""
        )

        with patch(
            "services.document_service.subprocess.run",
            return_value=completed
        ):
            service._run(
                [(Path("C:/docs/a.docx"), Path("C:/docs/a.pdf"))],
                lambda success, error: results.append((success, error))
            )

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0][0])
        self.assertIn("Word недоступен", results[0][1])

    def test_empty_batch_finishes_immediately(self):
        service = DocumentService()
        results = []

        service.convert_pdf([], on_done=lambda success, error: results.append(success))

        self.assertEqual(results, [True])


if __name__ == "__main__":
    unittest.main()
