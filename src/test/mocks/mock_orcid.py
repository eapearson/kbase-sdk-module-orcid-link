import json
from time import sleep

from orcidlink.lib import utils
from test.data.utils import load_test_data
from test.mocks.mock_server import MockService


class MockORCIDAPI(MockService):
    def do_GET(self):
        if self.path == "/0000-0003-4997-3076/record":
            test_data = load_test_data("orcid", "profile")
            self.send_json(test_data)

        elif self.path == "/0000-0003-4997-3076/email":
            test_data = load_test_data("orcid", "email")
            self.send_json(test_data)

        elif self.path == "/0000-0003-4997-3076/works":
            test_data = load_test_data("orcid", "works_x")
            self.send_json(test_data)

        elif self.path == "/0000-0003-4997-3076/works/1526002":
            work_record = load_test_data("orcid", "work_1526002")
            test_data = {
                "bulk": [
                    {
                        "work": work_record
                    }
                ]
            }
            self.send_json(test_data)

        elif self.path == "/0000-0003-4997-3076/works/bar":
            self.send_text("foobar")

        elif self.path == "/0000-0003-4997-3076/works/foo":
            error = {
                "response-code": 400,
                "developer-message": "The client application sent a bad request to ORCID. Full validation error: For input string: \"1526002x\"",
                "user-message": "The client application sent a bad request to ORCID.",
                "error-code": 9006,
                "more-info": "https://members.orcid.org/api/resources/troubleshooting"
            }
            self.send_json_error(error, status_code=400)

    def do_PUT(self):
        if self.path == "/0000-0003-4997-3076/work/1526002":
            test_data = load_test_data("orcid", "work_1526002")

            # simulates an updated last modified date.
            test_data['last-modified-date']['value'] = utils.current_time_millis()
            self.send_json(test_data)

    def do_POST(self):
        if self.path == "/0000-0003-4997-3076/works":
            new_work = json.loads(self.get_body_string())
            # TODO: just trust for now; simulate various error conditions
            # later.
            if new_work['bulk'][0]['work']['title']['title']['value'] == "trigger-500":
                self.send_text_error("AN ERROR", status_code=500)
            elif new_work['bulk'][0]['work']['title']['title']['value'] == "trigger-400":
                error_data = {
                    'user-message': "This is another error"
                }
                self.send_json_error(error_data, status_code=400)
            elif new_work['bulk'][0]['work']['title']['title']['value'] == "trigger-http-exception":
                # Note that this assumes the client timeout is < 1 sec. Tests
                # should set the timeout to 0.5sec.
                sleep(1)
                # don't bother with sending data, as the connection
                # will probably be dead by the time this is reached.
            else:
                test_work = load_test_data("orcid", "work_1526002")
                response_data = {
                    'bulk': [
                        {
                            'work': test_work
                        }
                    ]
                }
                self.send_json(response_data)


class MockORCIDAPIWithErrors(MockService):
    def do_GET(self):
        if self.path == "/0000-0003-4997-3076/record":
            test_data = load_test_data("orcid", "profile")
            self.send_json(test_data)
        elif self.path == "/0000-0003-4997-3076/email":
            test_data = load_test_data("orcid", "email")
            self.send_json(test_data)

        elif self.path == "/0000-0003-4997-3076/works":
            test_data = load_test_data("orcid", "orcid-works-error")
            self.send_json_error(test_data)

    def do_PUT(self):
        if self.path == "/0000-0003-4997-3076/work/1526002":
            test_data = load_test_data("orcid", "put_work_error")
            self.send_json_error(test_data)


class MockORCIDOAuth(MockService):
    def do_POST(self):
        # TODO: Reminder - switch to normal auth2 endpoint in config and here.
        if self.path == "/revoke":
            self.send_empty(status_code=200)
        elif self.path == "/token":
            test_data = {
                'access_token': "access_token",
                'token_type': "Bearer",
                'refresh_token': "refresh_token",
                'expires_in': 1000,
                'scope': "scope1",
                'name': "Foo Bear",
                'orcid': "abc123",
                'id_token': "id_token"
            }
            self.send_json(test_data)

    def do_GET(self):
        if self.path == "/authorize":
            # this is a browser-interactive url -
            # worth simulating?
            pass


class MockORCIDOAuth2(MockService):
    def do_POST(self):
        # TODO: Reminder - switch to normal auth2 endpoint in config and here.
        if self.path == "/revoke":
            self.send_empty(status_code=204)
