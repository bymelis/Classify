from copyleaks.copyleaks import Copyleaks
from copyleaks.models.submit.document import FileDocument
import os
from datetime import datetime
import uuid

class PlagiarismChecker:
    def __init__(self):
        self.copyleaks = Copyleaks()
        # Get credentials from environment variables
        self.api_email = os.environ.get('COPYLEAKS_EMAIL')
        self.api_key = os.environ.get('COPYLEAKS_API_KEY')

        # Validate credentials
        if not self.api_email or not self.api_key:
            raise ValueError("Copyleaks API credentials not found in environment variables. "
                             "Please set COPYLEAKS_EMAIL and COPYLEAKS_API_KEY environment variables.")

    def check_submission(self, file_path, student_name):
        try:
            # Login to Copyleaks
            try:
                self.copyleaks.login(self.api_email, self.api_key)
            except Exception as e:
                print(f"Login error: {str(e)}")
                raise Exception(f"Failed to login to Copyleaks: {str(e)}")

            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Submission file not found at: {file_path}")

            try:
                # Create file submission with configuration
                file_submission = FileDocument(
                    file_path,
                    {
                        'sandbox': False,
                        'webhook': None
                    }
                )

                # Generate a unique scan ID
                scan_id = str(uuid.uuid4())

                # Submit the file for scanning
                scan_result = self.copyleaks.submit_file(scan_id, file_submission)

                # Get the scan ID from the result
                scan_id = scan_result.scanned_document.scan_id

            except Exception as e:
                print(f"Scan error: {str(e)}")
                raise Exception(f"Failed to submit file for scanning: {str(e)}")

            return {
                'status': 'submitted',
                'scan_id': scan_id,
                'student_name': student_name,
                'submission_time': datetime.now().isoformat(),
                'message': 'Document submitted for plagiarism check'
            }

        except Exception as e:
            print(f"Plagiarism check error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_results(self, scan_id):
        """
        Get results for a submitted plagiarism scan.

        Args:
            scan_id (str): The ID of the scan to retrieve results for

        Returns:
            dict: A dictionary containing the scan results or status

        Raises:
            Exception: If there's an error retrieving the results
        """
        try:
            # Login to ensure we have an active session
            self.copyleaks.login(self.api_email, self.api_key)

            # Get the status of the scan
            status = self.copyleaks.get_scan_status(scan_id)

            if status.status == 'Completed':
                # Get the complete results
                results = self.copyleaks.get_results(scan_id)
                return {
                    'status': 'completed',
                    'results': results,
                    'message': 'Plagiarism check completed'
                }
            else:
                return {
                    'status': status.status.lower(),
                    'message': f'Scan is still in progress: {status.status}'
                }

        except Exception as e:
            print(f"Error retrieving results: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to retrieve results: {str(e)}'
            }
