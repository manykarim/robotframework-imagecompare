from skimage import io, measure, metrics, util, img_as_ubyte
from os.path import splitext, split
from decimal import *
from skimage.draw import rectangle
import json
import time
import re
import cv2
import os
import tempfile
from skimage.util import img_as_ubyte
from imutils.object_detection import non_max_suppression
import sys
EAST_CONFIDENCE=0.5

class CompareImage(object):

    ROBOT_LIBRARY_VERSION = 1.0
    DPI=200
    
    def __init__(self, image, **kwargs):
        tic = time.perf_counter()

        self.placeholder_file = kwargs.pop('placeholder_file', None)
        self.mask = kwargs.pop('mask', None)
        self.image = str(image)
        self.path, self.filename= split(image)
        self.filename_without_extension, self.extension = splitext(self.filename)
        self.opencv_images = []
        self.placeholders = []
        self.placeholder_mask = None
        self.placeholder_frame_width = 10
        self.tmp_directory = tempfile.TemporaryDirectory()
        self.diff_images = []
        self.threshold_images = []
        self.load_image_into_array()
        self.load_text_content_and_identify_masks()
        
    
        toc = time.perf_counter()
        print(f"Compare Image Object created in {toc - tic:0.4f} seconds")

        
    def identify_placeholders(self):
        if self.placeholder_file is not None:
            try:
                with open(self.placeholder_file, 'r') as f:
                    placeholders = json.load(f)
            except IOError as err:
                print("Placeholder File %s is not accessible", self.placeholder_file)
                print("I/O error: {0}".format(err))
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise
        elif self.mask is not None:
            try:
                placeholders = json.loads(self.mask)
            except:
                print('The mask {} could not be read as JSON'.format(self.mask))
        if isinstance(placeholders, list) is not True:
            placeholders = [placeholders]
        if (placeholders is not None):
            for placeholder in placeholders:
                placeholder_type = str(placeholder.get('type'))
                if (placeholder_type == 'coordinates'):
                    # print("Coordinate placeholder identified:")
                    # print(placeholder)
                    page = placeholder.get('page', 'all')
                    unit = placeholder.get('unit', 'px')
                    if unit == 'px':
                        x, y, h, w = (placeholder['x'], placeholder['y'], placeholder['height'], placeholder['width'])                    
                    elif unit == 'mm':
                        constant = self.DPI / 25.4
                        x, y, h, w = (int(placeholder['x']*constant), int(placeholder['y']*constant), int(placeholder['height']*constant), int(placeholder['width']*constant))
                    elif unit == 'cm':
                        constant = self.DPI / 2.54
                        x, y, h, w = (int(placeholder['x']*constant), int(placeholder['y']*constant), int(placeholder['height']*constant), int(placeholder['width']*constant))
                    placeholder_coordinates = {"page":page, "x":x, "y":y, "height":h, "width":w}
                    self.placeholders.append(placeholder_coordinates)

                elif (placeholder_type == 'area'):
                    page = placeholder.get('page', 'all')
                    location = placeholder.get('location', None)
                    percent = placeholder.get('percent', 10)
                    if page == 'all':
                        image_height = self.opencv_images[0].shape[0]
                        image_width = self.opencv_images[0].shape[1]
                    else:
                        image_height = self.opencv_images[page-1].shape[0]
                        image_width = self.opencv_images[page-1].shape[1]
                    if location == 'top':
                        height = int(image_height * percent / 100)
                        width = image_width
                        placeholder_coordinates = {"page":page, "x":0, "y":0, "height":height, "width":width}
                        pass
                    elif location == 'bottom':
                        height = int(image_height * percent / 100)
                        width = image_width
                        placeholder_coordinates = {"page":page, "x":0, "y":image_height - height, "height":height, "width":width}
                    elif location == 'left':
                        height = image_height
                        width = int(image_width * percent / 100)
                        placeholder_coordinates = {"page":page, "x":0, "y":0, "height":height, "width":width}
                    elif location == 'right':
                        height = image_height
                        width = int(image_width * percent / 100)
                        placeholder_coordinates = {"page":page, "x":image_width - width, "y":0, "height":height, "width":width}
                    self.placeholders.append(placeholder_coordinates)
    
    def get_image_with_placeholders(self, placeholders=None):
        if placeholders is None:
            placeholders = self.placeholders
        images_with_placeholders = self.opencv_images
        for placeholder in placeholders:
            if placeholder['page'] == 'all':
                for i in range(len(images_with_placeholders)):
                    start_point = (placeholder['x']-5, placeholder['y']-5)
                    end_point = (start_point[0]+placeholder['width']+10, start_point[1]+placeholder['height']+10)
                    try:
                        images_with_placeholders[i]=cv2.rectangle(images_with_placeholders[i], start_point, end_point, (255, 0, 0), -1)
                    except IndexError as err:
                        print("Page ", i, " does not exist in document")
                        print("Placeholder ", placeholder, " could not be applied")
            else:
                pagenumber = placeholder['page']-1
                start_point = (int(placeholder['x']-5), int(placeholder['y']-5))
                end_point = (int(start_point[0]+placeholder['width']+10), int(start_point[1]+placeholder['height']+10))
                try:
                    images_with_placeholders[pagenumber]=cv2.rectangle(images_with_placeholders[pagenumber], start_point, end_point, (255, 0, 0), -1)
                except IndexError as err:
                    print("Page ", pagenumber, " does not exist in document")
                    print("Placeholder ", placeholder, " could not be applied")
        return images_with_placeholders

    def load_image_into_array(self):
        if (os.path.isfile(self.image) is False):
            raise AssertionError('The file does not exist: {}'.format(self.image))
        self.DPI = 72
        img = cv2.imread(self.image)
        if img is None:
            raise AssertionError("No OpenCV Image could be created for file {} . Maybe the file is corrupt?".format(self.image))
        if self.opencv_images:
            self.opencv_images[0]= img
        else:
            self.opencv_images.append(img)

    def load_text_content_and_identify_masks(self):
        if (self.placeholder_file is not None) or (self.mask is not None):
            self.identify_placeholders()
        if self.placeholders != []:
            print('Identified Masks: {}'.format(self.placeholders))