import imp
import pytest
import requests

centos_cert = imp.load_source('centos_cert', 'centos-cert')


class MockResponse(object):
    def raise_for_status(self):
        pass

    @property
    def text(self):
        if self.url == 'https://accounts.centos.org/user/dogencert':
            return 'DUMMY-USER-CERT'
        if self.url == 'https://accounts.centos.org/ca/ca-cert.pem':
            return 'DUMMY-CA-CERT'
        raise NotImplementedError()


class RequestRecorder(object):
    """ Record args to requests.get() or requests.post() """
    def __call__(self, url, **kwargs):
        """ mocking requests.get() or requests.post() """
        self.response = MockResponse()
        self.response.url = url
        self.kwargs = kwargs
        return self.response


@pytest.fixture
def mock_get():
    return RequestRecorder()


@pytest.fixture
def mock_post():
    return RequestRecorder()


def test_download(monkeypatch, tmpdir, mock_get, mock_post):
    monkeypatch.delattr('requests.sessions.Session.request')
    monkeypatch.setenv('HOME', str(tmpdir))
    monkeypatch.setattr(requests, 'get', mock_get)
    monkeypatch.setattr(requests, 'post', mock_post)
    centos_cert.download_cert('myuser', 'mypass')

    assert mock_get.response.url == \
        'https://accounts.centos.org/ca/ca-cert.pem'
    assert mock_post.response.url == \
        'https://accounts.centos.org/user/dogencert'

    certfile = tmpdir.join('.centos.cert')
    assert certfile.check(file=1)
    assert certfile.read() == 'DUMMY-USER-CERT'
    assert oct(certfile.stat().mode & 0777) == '0600'

    cacertfile = tmpdir.join('.centos-server-ca.cert')
    assert cacertfile.check(file=1)
    assert cacertfile.read() == 'DUMMY-CA-CERT'

    uploadcafile = tmpdir.join('.centos-upload-ca.cert')
    assert uploadcafile.check(file=1)
    assert uploadcafile.read() == 'DUMMY-CA-CERT'
