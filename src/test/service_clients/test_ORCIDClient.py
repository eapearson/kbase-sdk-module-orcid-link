import json

import pytest
from orcidlink.lib import utils
from orcidlink.lib.config import ensure_config
from orcidlink.lib.responses import ErrorException
from orcidlink.service_clients.ORCIDClient import ORCIDAPIClient, ORCIDOAuthClient, orcid_api, orcid_api_url, \
    orcid_oauth
from test.mocks.mock_contexts import mock_orcid_api_service, mock_orcid_api_service_with_errors, \
    mock_orcid_oauth_service, \
    mock_orcid_oauth_service2, no_stderr


# from test.mocks.mock_orcid import MockORCIDAPI, MockORCIDAPIWithErrors, MockORCIDOAuth2


def load_test_data(filename: str):
    test_data_path = f"{utils.module_dir()}/src/test/service_clients/test_ORCIDClient/{filename}.json"
    with open(test_data_path) as fin:
        return json.load(fin)


@pytest.fixture(scope="function")
def test_filesystem(fs):
    fake_config = """
kbase:
  services:
    Auth2:
      url: http://127.0.0.1:9999/services/auth/api/V2/token
      tokenCacheLifetime: 300000
      tokenCacheMaxSize: 20000
    ServiceWizard:
      url: http://127.0.0.1:9999/services/service_wizard
  uiOrigin: https://ci.kbase.us
  defaults:
    serviceRequestTimeout: 60000
orcid:
  oauthBaseURL: https://sandbox.orcid.org/oauth
  baseURL: https://sandbox.orcid.org
  apiBaseURL: https://api.sandbox.orcid.org/v3.0
env:
  CLIENT_ID: 'REDACTED-CLIENT-ID'
  CLIENT_SECRET: 'REDACTED-CLIENT-SECRET'
  IS_DYNAMIC_SERVICE: 'yes'
    """
    fs.create_file("/kb/module/config/config.yaml", contents=fake_config)
    yield fs


@pytest.fixture(scope="function")
def my_fs(fs):
    yield fs


def test_orcid_api_url(test_filesystem):
    ensure_config(reload=True)
    value = orcid_api_url("path")
    assert isinstance(value, str)
    assert value == "https://api.sandbox.orcid.org/v3.0/path"


def test_orcid_api():
    value = orcid_api("token")
    assert isinstance(value, ORCIDAPIClient)
    assert value.access_token == "token"


def test_orcid_oauth():
    value = orcid_oauth("token")
    assert isinstance(value, ORCIDOAuthClient)
    assert value.access_token == "token"


def test_orcid_oauth():
    value = orcid_oauth("token")
    assert isinstance(value, ORCIDOAuthClient)
    assert value.access_token == "token"


def test_ORCIDOAuthClient_constructor():
    client = ORCIDOAuthClient(url="url", access_token="access_token")
    assert client.base_url == "url"
    assert client.access_token == "access_token"

    with pytest.raises(TypeError, match='the "access_token" named parameter is required'):
        ORCIDOAuthClient(url="url")

    with pytest.raises(TypeError, match='the "url" named parameter is required'):
        ORCIDOAuthClient(access_token="access_token")

    with pytest.raises(TypeError, match='the "url" named parameter is required'):
        ORCIDOAuthClient()


def test_ORCIDOAuthClient_url():
    client = ORCIDOAuthClient(url="url", access_token="access_token")
    url = client.url("foo")
    assert url == "url/foo"


def test_ORCIDOAuthClient_header():
    client = ORCIDOAuthClient(url="url", access_token="access_token")
    header = client.header()
    assert isinstance(header, dict)
    assert header.get('Accept') == "application/vnd.orcid+json"
    assert header.get('Content-Type') == 'application/vnd.orcid+json'
    assert header.get('Authorization') == "Bearer access_token"


class FakeResponse:
    def __init__(self, status_code: int = None, text: str = None):
        self.status_code = status_code
        self.text = text


def test_ORCIDAuthClient_make_exception():
    #
    # Error response in expected form, with a JSON response including "error_description"
    #
    client = ORCIDOAuthClient(url="url", access_token="access_token")
    fake_response = FakeResponse(status_code=123, text=json.dumps({"error_description": "bar"}))

    with pytest.raises(ErrorException, match="Error fetching data from ORCID Auth api") as ex:
        raise client.make_exception(fake_response, "source")

    assert ex.value.status_code == 400
    assert ex.value.error.data['source'] == "source"
    assert ex.value.error.data['originalResponseJSON']['error_description'] == "bar"
    assert 'originalResponseText' not in ex.value.error.data

    #
    # Error response in expected form, with a JSON response without "error_description";
    # Note that we don't make assumptions about any other field, and in this case, only
    # in the case of a 401 or 403 status code, in order to remove private information.
    #
    client = ORCIDOAuthClient(url="url", access_token="access_token")
    fake_response = FakeResponse(status_code=123, text=json.dumps({"foo": "bar"}))

    with pytest.raises(ErrorException, match="Error fetching data from ORCID Auth api") as ex:
        raise client.make_exception(fake_response, "source")

    assert ex.value.status_code == 400
    assert ex.value.error.data['source'] == "source"
    assert 'error_description' not in ex.value.error.data['originalResponseJSON']
    assert ex.value.error.data['originalResponseJSON']['foo'] == 'bar'
    assert 'originalResponseText' not in ex.value.error.data

    #
    # Error response in expected form, with a JSON response without "error_description";
    # Note that we don't make assumptions about any other field, and in this case, only
    # in the case of a 401 or 403 status code, in order to remove private information.
    #
    client = ORCIDOAuthClient(url="url", access_token="access_token")
    fake_response = FakeResponse(status_code=401, text=json.dumps({"error_description": "bar", "foo": "foe"}))

    with pytest.raises(ErrorException, match="Error fetching data from ORCID Auth api") as ex:
        raise client.make_exception(fake_response, "source")

    assert ex.value.status_code == 400
    assert ex.value.error.data['source'] == "source"
    assert 'error_description' not in ex.value.error.data['originalResponseJSON']
    assert ex.value.error.data['originalResponseJSON']['foo'] == 'foe'
    assert 'originalResponseText' not in ex.value.error.data

    #
    # Finally, we need to be able to handle non-json responses from ORCID.
    #
    client = ORCIDOAuthClient(url="url", access_token="access_token")
    fake_response = FakeResponse(status_code=401, text="just text, folks")

    with pytest.raises(ErrorException, match="Error fetching data from ORCID Auth api") as ex:
        raise client.make_exception(fake_response, "source")

    assert ex.value.status_code == 400
    assert ex.value.error.data['source'] == "source"
    assert 'originalResponseJSON' not in ex.value.error.data
    assert ex.value.error.data['originalResponseText'] == 'just text, folks'


def test_ORCIDOAuth_success():
    with no_stderr():
        with mock_orcid_oauth_service() as [_, _, url]:
            client = ORCIDOAuthClient(
                url=url,
                access_token="access_token"
            )
            response = client.revoke_token()
            assert response is None


def test_ORCIDOAuth_error():
    with no_stderr():
        with mock_orcid_oauth_service2() as [_, _, url]:
            client = ORCIDOAuthClient(
                url=url,
                access_token="access_token"
            )
            with pytest.raises(ErrorException, match="Error fetching data from ORCID Auth api"):
                client.revoke_token()


#
# ORCID API
#

def test_ORCIDAPIClient_constructor():
    client = ORCIDAPIClient(url="url", access_token="access_token")
    assert client.base_url == "url"
    assert client.access_token == "access_token"

    with pytest.raises(TypeError, match='the "access_token" named parameter is required'):
        ORCIDAPIClient(url="url")

    with pytest.raises(TypeError, match='the "url" named parameter is required'):
        ORCIDAPIClient(access_token="access_token")

    with pytest.raises(TypeError, match='the "url" named parameter is required'):
        ORCIDAPIClient()


def test_ORCIDAPIClient_url():
    client = ORCIDAPIClient(url="url", access_token="access_token")
    url = client.url("foo")
    assert url == "url/foo"


def test_ORCIDAPIClient_header():
    client = ORCIDAPIClient(url="url", access_token="access_token")
    header = client.header()
    assert isinstance(header, dict)
    assert header.get('Accept') == "application/vnd.orcid+json"
    assert header.get('Content-Type') == 'application/vnd.orcid+json'
    assert header.get('Authorization') == "Bearer access_token"


def test_ORCIDAPI_get_profile():
    with no_stderr():
        with mock_orcid_api_service() as [_, _, url]:
            orcid_id = "0000-0003-4997-3076"
            client = ORCIDAPIClient(
                url=url,
                access_token="access_token"
            )
            profile = client.get_profile(orcid_id)
            assert isinstance(profile, dict)
            assert profile['orcid-identifier']['path'] == orcid_id


def test_ORCIDAPI_get_email():
    with no_stderr():
        with mock_orcid_api_service() as [_, _, url]:
            orcid_id = "0000-0003-4997-3076"
            client = ORCIDAPIClient(
                url=url,
                access_token="access_token"
            )
            email = client.get_email(orcid_id)
            assert isinstance(email, dict)
            assert email['email'][0]['email'] == "eaptest40@mailinator.com"


def test_ORCIDAPI_get_works():
    with no_stderr():
        with mock_orcid_api_service() as [_, _, url]:
            orcid_id = "0000-0003-4997-3076"
            client = ORCIDAPIClient(
                url=url,
                access_token="access_token"
            )
            works = client.get_works(orcid_id)
            assert isinstance(works, dict)
            assert works['group'][0]['work-summary'][0]['put-code'] == 1487805


def test_ORCIDAPI_get_works_error():
    with no_stderr():
        with mock_orcid_api_service_with_errors() as [_, _, url]:
            orcid_id = "0000-0003-4997-3076"
            client = ORCIDAPIClient(
                url=url,
                access_token="access_token"
            )
            with pytest.raises(ErrorException, match="Error fetching data from ORCID Auth api") as ex:
                client.get_works(orcid_id)


def test_ORCIDAPI_save_work():
    with no_stderr():
        with mock_orcid_api_service() as [_, _, url]:
            orcid_id = "0000-0003-4997-3076"
            client = ORCIDAPIClient(
                url=url,
                access_token="access_token"
            )
            # work_update: WorkUpdate(
            #     putCode="1487805",
            #     title="foo",
            #     journal="bar",
            #     date="2001/02/03",??
            #     workType="baz",
            #     url="some url",
            # )
            # TODO: external ids too!
            put_code = 1526002
            work_update = load_test_data(f"work_{str(put_code)}")
            # don't change anything for now
            result = client.save_work(orcid_id, put_code, work_update)
            assert isinstance(result, dict)
            assert result['put-code'] == put_code


def test_ORCIDAPI_save_work_error():
    #
    # We use the mock ORCID server which returns errors
    #
    with no_stderr():
        with mock_orcid_api_service_with_errors() as [_, _, url]:
            orcid_id = "0000-0003-4997-3076"
            #
            # The client we are testing will access the mock server above since we are
            # using the base_url it calculates, which uses IP 127.0.0.1 as specified in the
            # constructor, and a randomly generated port.
            #
            client = ORCIDAPIClient(
                url=url,
                access_token="access_token"
            )
            with pytest.raises(ErrorException, match="Error fetching data from ORCID Auth api") as ex:
                put_code = 1526002
                work_update = load_test_data(f"work_{str(put_code)}")
                # don't change anything for now
                client.save_work(orcid_id, put_code, work_update)
            assert ex.value.error.data['originalResponseJSON']['response-code'] == 400
