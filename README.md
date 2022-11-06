# Charite-Scripts
Some useful scripts for special websites while studying medicine at Charité Universitätsmedizin Berlin 

## LLP
This script will show you available (bookable) tutorials on the *LLP* website and allows booking on the commandline

1. First you enter your *email* (you can enter it without @charite.de)
2. You enter your *password*
3. If you did everything correctly you get an info about your current points, currently booked tutorials and a list of available tutorials
4. If you didnt enter your credentials correctly you can still continue and you will be able to see the tutorials (booking will redirect you to your browser)
5. Enter the number of the tutorial you want to book
6. Enter the slot you want to book
7. Have fun!

## Thiemedownload
This script is old and only works when you are in the OpenVPN network (shibboleth isnt implemented yet). It allows you to download a whole book from [Thieme](https://eref.thieme.de/).

### TODO:
* Add the option to merge without duplicates
* Add Shibboleth login support

### Instructions:
1. You have to change the default savePath variable in python first
2. Search a book on Thieme and find your id 
    + for example 123456 is the id of https://eref.thieme.de/ebooks/123456)
4. enter the id
5. enter a foldername (if it doesn't exist, it will be created)
6. Choose if you wan't to merge all chapter-PDFs 
    + **CAVE: This will sometimes create PDFs with duplicate pages, because some PDFs have overlap**
7. Enjoy your ebook!
