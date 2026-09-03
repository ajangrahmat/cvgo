# Publishing CVGO to PyPI

This guide is used so users can install CVGO with:

```bash
pip install cvgo
```

## 1. Check the project name

Open the following page:

```text
https://pypi.org/project/cvgo/
```

A 404 page usually means there is no public release yet under that name.
However, the final confirmation is always determined by PyPI at the first upload,
because a name can be reserved or too similar to another project.

## 2. Create accounts

Create two separate accounts:

- TestPyPI: https://test.pypi.org/account/register/
- PyPI: https://pypi.org/account/register/

Enable 2FA and create an API token. Do not place the token in source code,
Git repositories, README files, or other shared files.

## 3. Prepare the environment

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 4. Run tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q src examples tests
python -m cvgo check
```

Also run manual checks with a webcam, Arduino, and one Telegram chat in a test
environment using MediaPipe 0.10.21 before release. Keep Telegram tokens only in
environment variables and do not include them in source, logs, or distribution
artifacts.

Prepare and test the model download flow before release:

```bash
python -c "import cvgo as go; go.download_model('object_detection')"
python -c "import cvgo as go; go.download_model('gesture_recognizer')"
```

Models are not included in the wheel. `ObjectDetector` and `GestureRecognizer`
download the official MediaPipe models once and then reuse them from cache.

## 5. Build the distribution

Make sure the old `dist` folder is not reused, then run:

```bash
python -m build
python -m twine check dist/*
```

A normal result includes:

```text
dist/cvgo-0.2.1.tar.gz
dist/cvgo-0.2.1-py3-none-any.whl
```

## 6. Test on TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

Username for the token:

```text
__token__
```

The password is the full TestPyPI API token starting with `pypi-`.

Test the installation in a fresh virtual environment. Dependencies still come from
main PyPI because TestPyPI does not always mirror every package:

```bash
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  cvgo
```

Then validate:

```bash
python -c "import cvgo; print(cvgo.__version__)"
```

## 7. Upload to PyPI

If TestPyPI succeeds:

```bash
python -m twine upload dist/*
```

After the release appears, test again in a fresh virtual environment:

```bash
pip install cvgo
python -c "import cvgo; print(cvgo.__version__)"
```

## 8. Next release

Files with the same version number cannot be uploaded again. If a revision is
needed, update the central version file, for example:

```python
# src/cvgo/_version.py
__version__ = "0.2.2"
```

`pyproject.toml` reads this value dynamically, so this is the only package
version field to edit. Then rebuild and upload the new version.

## Core CVGO versions

CVGO pins the tested core stack:

```toml
numpy==1.26.4
opencv-contrib-python==4.11.0.86
mediapipe==0.10.21
```

This version pinning keeps the `mp.solutions` API, models, `cv2` module, and test
results consistent across developer machines and participant machines. Use a
separate virtual environment so exact pins do not conflict with other projects that
need different OpenCV or NumPy versions.
