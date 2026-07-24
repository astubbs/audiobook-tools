# Sample audio fixtures

Tiny, **non-copyrighted** spoken-word MP3s used by the end-to-end integration tests
(`tests/test_integration.py`). The audio was generated from original text written for
this project using macOS `say`, then encoded to small mono 32 kbps MP3s:

```sh
say -o /tmp/ch.aiff "<original text>"
ffmpeg -y -i /tmp/ch.aiff -ac 1 -codec:a libmp3lame -b:a 32k "NN - Title.mp3"
```

Filenames follow the `NN - Title.mp3` convention the MP3 chapterizer expects, so the
integration test can assert exact chapter titles and ordering. These files are safe to
commit and redistribute (original content, no third-party works).
