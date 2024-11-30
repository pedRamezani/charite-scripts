# Charite-Scripts
Some useful scripts for special websites while studying medicine at [Charité - Universitätsmedizin Berlin](https://www.charite.de/).

## PJ Portal Change Notifier `lambda_function_pj_portal.py`
**LAST CHECKED TO SEE IF THIS WAS WORKING: November 30th, 2024**

This is an [AWS Lambda](https://aws.amazon.com/lambda/) function to check the availability of free PJ elective slots in the [PJ-Portal](https://www.pj-portal.de/).

You can read more about this script and how to setup your own AWS account for this task in my [blog post](https://www.pedramramezani.de/posts/aws-lambda-scraper/).

## LLP Booker `llp.py`
**LAST CHECKED TO SEE IF THIS WAS WORKING: November 30th, 2024**

This script shows you the available (bookable) tutorials on the [*LLP* website](https://lernziele.charite.de) and allows you to book them on the command line. This command can't unbook a tutorial and is designed to be used when new tutorials are released, as there is usually a noticeable slowdown when everyone tries to visit the site at the same time. This script reduces the bandwidth required.

1. First you enter your *email* (you can enter it without "@charite.de")
2. You enter your *password*
3. If you did everything correctly you get an info about your current tutorial points, currently booked tutorials and a list of available tutorials
4. If you didnt enter your credentials correctly you can still continue and you will be able to see the tutorials (booking will redirect you to your browser)
5. Enter the number of the tutorial you want to book
6. Enter the slot you want to book
7. ???
8. Have fun with the tutorial!

## Thieme Book Download `thiemedownload.py`
**LAST CHECKED TO SEE IF THIS WAS WORKING: November 6th, 2022**

This script is old and only works when you are in the OpenVPN network (shibboleth isnt implemented yet). It allows you to download a whole book from [Thieme](https://eref.thieme.de/).

### TODO:
* Add the option to merge without duplicates
* Add Shibboleth login support

### Instructions:
1. You have to change the default savePath variable in python first
2. Search a book on Thieme and find your ID 
    + for example `123456` is the id of https://eref.thieme.de/ebooks/123456)
4. Enter the ID
5. Enter a foldername (if it doesn't exist, it will be created)
6. Choose if you wan't to merge all chapter-PDFs 
    + **CAVE: This will sometimes create PDFs with duplicate pages, because some PDFs have a overlap**
7. Enjoy your ebook!
