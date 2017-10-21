from ..sessionfactory import SessionFactory

from tqdm import tqdm


class SimpleHttpDownloader(SessionFactory):
    def __init__(self):
        super().__init__()

    def download_file(self, name, url, headers, filename):
        r = super().getSession().get(
            url,
            allow_redirects=True,
            headers=headers,
            stream=True
        )

        if r.status_code != 200:
            with open("errfile.html", "wb") as f:
                f.write(r.content)
            raise RuntimeError(
                "Failed downloading file due to non 200 return code. "
                "Return code was " + str(r.status_code)
            )

        total_size = int(r.headers.get("content-length", 0))
        with tqdm(desc=name, total=total_size, unit='B',
                  unit_scale=True, miniters=1) as bar:
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(32*1024):
                    bar.update(len(chunk))
                    fd.write(chunk)
