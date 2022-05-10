*** Settings ***
Library    ImageCompare    show_diff=true    take_screenshots=true    screenshot_format=png    #pdf_rendering_engine=ghostscript
Library    Collections

*** Variables ***
${TESTDATA}    ${CURDIR}${/}testdata


*** Test Cases ***
Compare two different Beach images
    Run Keyword And Expect Error    The compared images are different.    Compare Images    ${TESTDATA}/Beach_left.jpg    ${TESTDATA}/Beach_right.jpg

Compare two different Farm images
    Run Keyword And Expect Error    The compared images are different.    Compare Images    ${TESTDATA}/Farm_left.jpg    ${TESTDATA}/Farm_right.jpg

Compare two equal Beach images
    Compare Images    ${TESTDATA}/Beach_left.jpg    ${TESTDATA}/Beach_left.jpg

Compare two different Beach images with mask
    Compare Images    ${TESTDATA}/Beach_left.png    ${TESTDATA}/Beach_date.png    placeholder_file=${TESTDATA}/area_mask.json
