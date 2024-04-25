# SURVEPY
SURVEPY allows you to automatically process the answers to paper surveys/questionnaires using color recognition.

I originated the idea following an undergraduate research internship where I had to process a handful of paper questionnaires, consisting of manually filling 20,000+ cells on an excel sheet.

The program works as follows:
1) Response areas are detected for each item, using the red dots that delimit the response options of each item.
2) Specific response areas are detected for each response option of each item.
3) The participant answer to each item is defined as the specific response area that contains the smallest number of white pixels.

Concrete example: https://i.imgur.com/5ZBaQAa.jpeg

The settings.xlsx file gives you the ability to set specific instructions as to how each item should be treated (i.e., reverse-scoring, number of response options)
