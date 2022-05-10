"""
# ImageCompare Library for Robot Framework®

A library for simple screenshot comparison.
Supports image files like .png and .jpg.

Image Parts can be ignored via simple coordinate masks or area masks.

See [Keyword Documentation](https://manykarim.github.io/robotframework-imagecompare/imagecompare.html) for more information.

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
"""

from skimage import metrics
import imutils
import cv2
import time
import shutil
import os
import uuid
import numpy as np
from pathlib import Path
from robot.libraries.BuiltIn import BuiltIn
import re
from concurrent import futures
from robot.api.deco import keyword, library
import json
import math
from .CompareImage import CompareImage

@library
class ImageCompare(object):

    ROBOT_LIBRARY_VERSION = 0.2
    DPI = 200
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    BOTTOM_LEFT_CORNER_OF_TEXT = (20,60)
    FONT_SCALE = 0.7
    FONT_COLOR = (255,0,0)
    LINE_TYPE = 2
    REFERENCE_LABEL = "Expected Result (Reference)"
    CANDIDATE_LABEL = "Actual Result (Candidate)"

    def __init__(self, **kwargs):
        self.threshold = kwargs.pop('threshold', 0.0000)
        self.SCREENSHOT_DIRECTORY = Path("screenshots/")
        self.DPI = int(kwargs.pop('DPI', 200))
        self.take_screenshots = bool(kwargs.pop('take_screenshots', False))
        self.show_diff = bool(kwargs.pop('show_diff', False))
        self.screenshot_format = kwargs.pop('screenshot_format', 'jpg')
        if not (self.screenshot_format == 'jpg' or self.screenshot_format == 'png'):
             self.screenshot_format == 'jpg'

        built_in = BuiltIn()
        try:
            self.OUTPUT_DIRECTORY = built_in.get_variable_value('${OUTPUT DIR}')
            self.reference_run = built_in.get_variable_value('${REFERENCE_RUN}', False)
            self.PABOTQUEUEINDEX = built_in.get_variable_value('${PABOTQUEUEINDEX}')
            os.makedirs(self.OUTPUT_DIRECTORY/self.SCREENSHOT_DIRECTORY, exist_ok=True)
        except:
            print("Robot Framework is not running")
            self.OUTPUT_DIRECTORY = Path.cwd()
            os.makedirs(self.OUTPUT_DIRECTORY / self.SCREENSHOT_DIRECTORY, exist_ok=True)
            self.reference_run = False
            self.PABOTQUEUEINDEX = None
    
    @keyword    
    def compare_images(self, reference_image, test_image, **kwargs):
        """Compares the documents/images ``reference_image`` and ``test_image``.

        ``**kwargs`` can be used to add settings for ``placeholder_file``
        
        Result is passed if no visual differences are detected. 
        
        ``reference_image`` and ``test_image`` may be image files, e.g. png, jpg, or tiff.


        Examples:
        | = Keyword =    |  = reference_image =  | = test_image =       |  = **kwargs = | = comment = |
        | Compare Images | reference.png | candidate.png |                              | #Performs a pixel comparison of both files |
        | Compare Images | reference.png (not existing)  | candidate.png |              | #Will always return passed and save the candidate.pdf as reference.pdf |
        | Compare Images | reference.png | candidate.png | placeholder_file=mask.json   | #Performs a pixel comparison of both files and excludes some areas defined in mask.json |
        | Compare Images | reference.pdf | candidate.pdf | contains_barcodes=${true}    | #Identified barcodes in documents and excludes those areas from visual comparison. The barcode data will be checked instead |
                
        """
        #print("Execute comparison")
        #print('Resolution for image comparison is: {}'.format(self.DPI))

        reference_collection = []
        compare_collection = []
        detected_differences = []

        placeholder_file = kwargs.pop('placeholder_file', None)
        mask = kwargs.pop('mask', None)
        self.DPI = int(kwargs.pop('DPI', self.DPI))

        if self.reference_run and (os.path.isfile(test_image) == True):
            shutil.copyfile(test_image, reference_image)
            print('A new reference file was saved: {}'.format(reference_image))
            return
            
        if (os.path.isfile(reference_image) is False):
            raise AssertionError('The reference file does not exist: {}'.format(reference_image))

        if (os.path.isfile(test_image) is False):
            raise AssertionError('The candidate file does not exist: {}'.format(test_image))

        with futures.ThreadPoolExecutor(max_workers=2) as parallel_executor:
            reference_future = parallel_executor.submit(CompareImage, reference_image, placeholder_file=placeholder_file, DPI=self.DPI, mask=mask)
            candidate_future = parallel_executor.submit(CompareImage, test_image, DPI=self.DPI)
            reference_compare_image = reference_future.result()
            candidate_compare_image = candidate_future.result()
        
        tic = time.perf_counter()
        if reference_compare_image.placeholders != []:
            candidate_compare_image.placeholders = reference_compare_image.placeholders
            with futures.ThreadPoolExecutor(max_workers=2) as parallel_executor:
                reference_collection_future = parallel_executor.submit(reference_compare_image.get_image_with_placeholders)
                compare_collection_future = parallel_executor.submit(candidate_compare_image.get_image_with_placeholders)
                reference_collection = reference_collection_future.result()
                compare_collection = compare_collection_future.result()
        else:
            reference_collection = reference_compare_image.opencv_images
            compare_collection = candidate_compare_image.opencv_images

        if len(reference_collection)!=len(compare_collection):
            print("Pages in reference file:{}. Pages in candidate file:{}".format(len(reference_collection), len(compare_collection)))
            for i in range(len(reference_collection)):
                cv2.putText(reference_collection[i],self.REFERENCE_LABEL, self.BOTTOM_LEFT_CORNER_OF_TEXT, self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.LINE_TYPE)
                self.add_screenshot_to_log(reference_collection[i], "_reference_page_" + str(i+1))
            for i in range(len(compare_collection)):
                cv2.putText(compare_collection[i],self.CANDIDATE_LABEL, self.BOTTOM_LEFT_CORNER_OF_TEXT, self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.LINE_TYPE)
                self.add_screenshot_to_log(compare_collection[i], "_candidate_page_" + str(i+1))
            raise AssertionError('Reference File and Candidate File have different number of pages')
        
        check_difference_results = []
        with futures.ThreadPoolExecutor(max_workers=8) as parallel_executor:
            for i, (reference, candidate) in enumerate(zip(reference_collection, compare_collection)):
                check_difference_results.append(parallel_executor.submit(self.check_for_differences, reference, candidate, i, detected_differences))
        for result in check_difference_results:
            if result.exception() is not None:
                raise result.exception()
        for difference in detected_differences:

            if (difference):
                print("The compared images are different")
                raise AssertionError('The compared images are different.')

        print("The compared images are equal")

        toc = time.perf_counter()
        print(f"Visual Image comparison performed in {toc - tic:0.4f} seconds")

    def get_images_with_highlighted_differences(self, thresh, reference, candidate, extension=10):
        
        #thresh = cv2.dilate(thresh, None, iterations=extension)
        thresh = cv2.dilate(thresh, None, iterations=extension)
        thresh = cv2.erode(thresh, None, iterations=extension)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # loop over the contours
        for c in cnts:
            # compute the bounding box of the contour and then draw the
            # bounding box on both input images to represent where the two
            # images differ
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(reference, (x, y), (x + w, y + h), (0, 0, 255), 4)
            cv2.rectangle(candidate, (x, y), (x + w, y + h), (0, 0, 255), 4)
        return reference, candidate, cnts

    def get_diff_rectangle(self, thresh):
        points = cv2.findNonZero(thresh)
        (x, y, w, h) = cv2.boundingRect(points)
        return x, y, w, h

    def add_screenshot_to_log(self, image, suffix):
        screenshot_name = str(str(uuid.uuid1()) + suffix + '.{}'.format(self.screenshot_format))
        
        if self.PABOTQUEUEINDEX is not None:
            rel_screenshot_path = str(self.SCREENSHOT_DIRECTORY / '{}-{}'.format(self.PABOTQUEUEINDEX, screenshot_name))
        else:
            rel_screenshot_path = str(self.SCREENSHOT_DIRECTORY / screenshot_name)
            
        abs_screenshot_path = str(self.OUTPUT_DIRECTORY/self.SCREENSHOT_DIRECTORY/screenshot_name)
        
        if self.screenshot_format == 'jpg':
            cv2.imwrite(abs_screenshot_path, image, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        else:
            cv2.imwrite(abs_screenshot_path, image)

        print("*HTML* "+ "<a href='" + rel_screenshot_path + "' target='_blank'><img src='" + rel_screenshot_path + "' style='width:50%; height: auto;'/></a>")

    def overlay_two_images(self, image, overlay, ignore_color=[255,255,255]):
        ignore_color = np.asarray(ignore_color)
        mask = ~(overlay==ignore_color).all(-1)
        # Or mask = (overlay!=ignore_color).any(-1)
        out = image.copy()
        out[mask] = image[mask] * 0.5 + overlay[mask] * 0.5
        return out

    def check_for_differences(self, reference, candidate, i, detected_differences):
        images_are_equal = True
        with futures.ThreadPoolExecutor(max_workers=2) as parallel_executor:
            grayA_future = parallel_executor.submit(cv2.cvtColor, reference, cv2.COLOR_BGR2GRAY)
            grayB_future = parallel_executor.submit(cv2.cvtColor, candidate, cv2.COLOR_BGR2GRAY)
            grayA = grayA_future.result()
            grayB = grayB_future.result()

        if reference.shape[0] != candidate.shape[0] or reference.shape[1] != candidate.shape[1]:
            self.add_screenshot_to_log(reference, "_reference_page_" + str(i+1))
            self.add_screenshot_to_log(candidate, "_candidate_page_" + str(i+1))
            raise AssertionError(f'The compared images have different dimensions:\nreference:{reference.shape}\ncandidate:{candidate.shape}')
        
        # compute the Structural Similarity Index (SSIM) between the two
        # images, ensuring that the difference image is returned
        (score, diff) = metrics.structural_similarity(grayA, grayB, gaussian_weights=True, full=True)
        score = abs(1-score)
        
        if self.take_screenshots:
            # Not necessary to take screenshots for every successful comparison
            self.add_screenshot_to_log(np.concatenate((reference, candidate), axis=1), "_page_" + str(i+1) + "_compare_concat")
               
        if (score > self.threshold):
        
            diff = (diff * 255).astype("uint8")

            thresh = cv2.threshold(diff, 0, 255,
                cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            
            reference_with_rect, candidate_with_rect , cnts= self.get_images_with_highlighted_differences(thresh, reference.copy(), candidate.copy(), extension=int(os.getenv('EXTENSION', 2)))
            blended_images = self.overlay_two_images(reference_with_rect, candidate_with_rect)
            
            cv2.putText(reference_with_rect,self.REFERENCE_LABEL, self.BOTTOM_LEFT_CORNER_OF_TEXT, self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.LINE_TYPE)
            cv2.putText(candidate_with_rect,self.CANDIDATE_LABEL, self.BOTTOM_LEFT_CORNER_OF_TEXT, self.FONT, self.FONT_SCALE, self.FONT_COLOR, self.LINE_TYPE)
            
            self.add_screenshot_to_log(np.concatenate((reference_with_rect, candidate_with_rect), axis=1), "_page_" + str(i+1) + "_rectangles_concat")
            self.add_screenshot_to_log(blended_images, "_page_" + str(i+1) + "_blended")

            if self.show_diff:
                self.add_screenshot_to_log(np.concatenate((diff, thresh), axis=1), "_page_" + str(i+1) + "_diff")

            images_are_equal=False
            
            if images_are_equal is not True:
                detected_differences.append(True)
