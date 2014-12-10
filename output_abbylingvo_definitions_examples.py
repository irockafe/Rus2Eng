# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import subprocess
import urllib
import urllib2
from sys import argv
import time
from random import randrange
import csv
import requests

'''
CALL: python script word_list tags 
INPUT: csv file containing one russian word per line
OUTPUT: tab-delimited file containing:
Russian word, English translations, Russian sentence,
English sentence, user-defined tags

This format can be imported to Anki.

If you run into a captcha, just open a browser, reload 
http://www.lingvo.ua/ru and submit the captcha. Then
re-run the command, no change to the commands argument
are necessary
'''

def get_definitions_example_link(html):
   '''
   INPUT: a ABBY Lingvo search page
   (Russian to English). 
   OUTPUT: A link to examples for the most common definition and
   a list containing the first 3 definitions: 
   those in (<span> class='translation'</span>)
   '''
   soup = BeautifulSoup(html)
   #Translations are under the title 'Показать примеры употребления'
   a_tags = soup.find_all('a', {'title': 'Показать примеры употребления'})
   print '\nNumber of usage examples:', len(a_tags)
   #An error occurs, most likely a captcha
   if not a_tags:
      return [], []
   #get the translations and links as a list
   link_list = []
   translation_list = []
   for tag in a_tags:
      translation = tag.find('span', {'class':'translation'})
      #not all a_tags have a class='translation' attribute
      if translation:
         english_word = translation.text
         link = tag['href']
         #make sure it's a full URL
         if 'http://www.lingvo.ua' not in link:
            link = 'http://www.lingvo.ua' + tag['href']
         link_list.append(link)
         translation_list.append(english_word)
   return link_list[0], translation_list[0:2]
   
def get_examples_under_x_characters(url, character_limit):
   '''
   INPUT: Url to abby-lingvo page containing sample sentences
          and a character limit so you don't pick up a mountain of text
   OUTPUT: 2 strings: one russian sample and its english equivalent
   '''

   webpage = urllib2.urlopen(url).read()
   soup = BeautifulSoup(webpage)
   rus_example_htmls = soup.find_all('div', {"class": "l-examples__text js-first-source-text"})
   eng_example_htmls = soup.find_all('div', {"class": "l-examples__text js-second-source-text"})

   rus_example = ''
   eng_example = ''
   for entry_number, entry in enumerate(rus_example_htmls):
      #remove html stuff and the lead/trailing /t/r/n characters
      entry = entry.get_text().strip()
      #print entry
      #print len(entry)
      
      if len(entry) <= character_limit:
         print 'Found it!'
         rus_example = entry
         #grab the English equivalent to the Russian phrase 
         #and exit the loop
         eng_example = eng_example_htmls[entry_number].get_text().strip()
         break
      else:
         print 'Too long! Moving onto round %s' % (entry_number+1)
   return rus_example, eng_example

def list_to_text(list_text):
   txt = ''
   for entry in list_text:
      txt += entry + ', '
   txt = txt.strip(', ')
   return txt

#Must use a csv file, with nothing but words
script, word_list_csv, week_number = argv
final_output = open('flashcard_list_%s.txt' % week_number, 'a')
#If the script finds no translations, it will move the old 
#word list to a new filename, and output the remaining untranslated
#words to the original filename
kill_script = ''
with open(word_list_csv, 'r') as word_list:
   reader = csv.reader(word_list)
   for row in reader:
      if kill_script:
         #write remaining rows to a new file
         writer.writerow(row)
         continue
      word = row[0]
      print '\n' + word
      data = urllib.urlencode({'searchText' : word})
      url = 'http://www.lingvo.ua/ru/Translate/en-ru/'
      full_url = url + '?' + data
      response = urllib2.urlopen(full_url)
      html_file = response.read() 
      
      #Get the first translations and a link to get sentence samples
      example_link, translation_list = get_definitions_example_link(html_file)
      #If an error occurred, and no translations were found
      if not translation_list:
         print '\nCAPTCHA, PROBABLY\n'
         print 'attempted url', full_url
         kill_script = 'kill it'
         #move the old file to a different name
         subprocess.call('mv %s %s_OLD' % (word_list_csv, word_list_csv), shell=True)
         #write remaining words to new file
         #with same name as original
         new_file = open(word_list_csv, 'a')
         writer = csv.writer(new_file)
         writer.writerow(row)
         continue
      print '\n translation list', translation_list
      translation = list_to_text(translation_list)
      print translation

      #Sleep for a variable time so they don't kick you off the site as quickly
      wait_time = randrange(5)
      time.sleep(wait_time)
      
      #if there is a link, get sample sentences
      if example_link != '':
         rus_example, eng_example = get_examples_under_x_characters(example_link, 120)
      else:
         rus_example = ''
         eng_example = ''      
      print '\n word:', word, '\n translation:', translation.encode('utf-8'), '\n russian:', rus_example.encode('utf-8'), '\n english:', eng_example.encode('utf-8')
      
      #Step 5 - Output the word, translations, sample sentences, and tags to a new csv file

      final_output.write('%s\t%s\t%s\t%s\t%s\n'.encode('utf8') % (word, translation.encode('utf-8'), rus_example.encode('utf-8'), eng_example.encode('utf-8'), week_number))

if kill_script:
   raise Warning('No translations present - You probably need to enter a captcha')


new_file.close()
final_output.close()
      #open_file.close()
      