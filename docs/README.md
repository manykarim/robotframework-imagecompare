
# ImageCompare Library for Robot Framework®

A library for simple screenshot comparison.
Supports image files like .png and .jpg.

Image Parts can be ignored via simple coordinate masks or area masks.

## Install robotframework-imagecompare

### Installation via `pip`

* `pip install --upgrade robotframework-imagecompare`

## Examples

Check the `/atest/Compare.robot` test suite for some examples.

### Testing with [Robot Framework](https://robotframework.org)
```RobotFramework
*** Settings ***
Library    ImageCompare

*** Test Cases ***
Compare two Images and highlight differences
    Compare Images    Reference.jpg    Candidate.jpg
```

### Use masks/placeholders to exclude parts from visual comparison

```RobotFramework
*** Settings ***
Library    ImageCompare

*** Test Cases ***
Compare two Images and ignore parts by using masks
    Compare Images    Reference.jpg    Candidate.jpg    placeholder_file=masks.json

Compare two PDF Docments and ignore parts by using masks
    Compare Images    Reference.jpg    Candidate.jpg    placeholder_file=masks.json
```
#### Different Mask Types to Ignore Parts When Comparing
##### Areas, Coordinates
```python
[
    {
    "page": "1",
    "name": "Top Border",
    "type": "area",
    "location": "top",
    "percent":  5
    },
    {
    "page": "1",
    "name": "Left Border",
    "type": "area",
    "location": "left",
    "percent":  5
    },
    {
    "page": 1,
    "name": "Top Rectangle",
    "type": "coordinates",
    "x": 0,
    "y": 0,
    "height": 10,
    "width": 210,
    "unit": "mm"
    }
]
```
## More info will be added soon
