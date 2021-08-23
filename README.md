# Matrix Portal: MTA

Code written for [Adafruit's Matrix Portal board](https://www.adafruit.com/product/4745) to display stylish transit info for selected MTA train lines on a 64x32 RGB Matrix.

## Quickstart

This project assumes a `SECRETS.py` file in the project root directory. This `SECRETS.py` file needs to be constructed with the following dict:

```python
TODO
```

I use watchman to automatically copy my code.py and the correct libraries to the MatrixPortal. This triggers a live/reload via CircuitPy

```shell
watchman watch .
watchman -- trigger . deploy -- sh copy.sh
```
