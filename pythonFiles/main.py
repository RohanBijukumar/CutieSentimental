#-----------------BASIC IMPORTS
import os
import requests
import numpy as np
from keep_alive import keep_alive

#-----------------DISCORD BOT
import discord
import openai
import matplotlib.pyplot as plt

#-----------------SMILE DETECTION IMPORTS
import cv2
from PIL import Image
from io import BytesIO

#-----------------SMILE DETECTION INITIALIZERS
cascade_face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cascade_eye = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
cascade_smile = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

#-----------------SMILE DETECTION ALGORITHM
def detection(grayscale,img):
    face=cascade_face.detectMultiScale(grayscale,1.3,5)
    is_smile = False
    for (x_face,y_face,w_face,h_face) in face:
        cv2.rectangle(img,(x_face,y_face),(x_face+w_face,y_face+h_face),(255,130,0),2)
        ri_grayscale=grayscale[y_face:y_face+h_face,x_face:x_face+w_face]
        ri_color=img[y_face:y_face+h_face,x_face:x_face+w_face]

        eye=cascade_eye.detectMultiScale(ri_grayscale,1.1,10)
        for(x_eye,y_eye,w_eye,h_eye) in eye:
            cv2.rectangle(ri_color,(x_eye,y_eye),(x_eye+w_eye,y_eye+h_eye),(0,180,60),2)
        smile=cascade_smile.detectMultiScale(ri_grayscale, 1.7, 20)
        print(smile)
        print(type(smile))
        if "<class 'tuple'>" not in str(type(smile)):
          is_smile = True
    return is_smile

#------------------DISCORD INTENTS
intents = discord.Intents.all()
client = discord.Client(intents=intents)

#------------------OPENAI KEY 
openai.api_key = os.getenv("OPENAI_API_KEY")

#------------------OPENAI ALGORITHM
def return_sentiment(text):
  response = openai.Completion.create(
    model="text-davinci-002",
    prompt=
    f'''Decide whether a Tweet's sentiment is positive, neutral, or negative.\n\nTweet: \"{text}"\nSentiment:''',
    temperature=0,
    max_tokens=60,
    top_p=1.0,
    frequency_penalty=0.5,
    presence_penalty=0.0)
  answer = str(response['choices'][0]['text'])
  return answer

#------------------CLIENT GLOBAL VARIABLES
messages = []
messagesTime = []
sentiment_history = []
count = 0

#------------------BOT LOGS ON
@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))

#------------------MESSAGE SENT
@client.event
async def on_message(msg):
  global count
  if msg.author == client.user: #BOT SPEAKING
    return
  else: #USER SPEAKS
    if msg.content.startswith(">"):
      pass
    else:
      messages.append(msg.content.lower())
      messagesTime.append(msg.created_at)
      print(msg.created_at)

  sentiment = return_sentiment(msg.content)
  if "ositive" in sentiment:
    sentiment_history.append(1)
  elif "egative" in sentiment:
    sentiment_history.append(-1)
  elif "eutral" in sentiment:
    sentiment_history.append(0)
  if msg.content.startswith('>vizSent'):
    window_size = 5
    
    i = 0
    # Initialize an empty list to store moving averages
      
    # Loop through the array to consider
    # every window of size 3
    moving_averages = []
    while i < len(sentiment_history) - window_size:
        
        # Store elements from i to i+window_size
        # in list to get the current window
        window = sentiment_history[i : i + window_size]
      
        # Calculate the average of current window
        window_average = round(sum(window) / window_size, 2)
          
        # Store the average of current
        # window in moving average list
        moving_averages.append(window_average)
          
        # Shift window to right by one position
        i += 1

    plt.ylim(-1, 1)
    plt.title('Server Mood Over Time')
    plt.ylabel('Sentiment (-1 = Negative, 1 = Positive)')
    plt.xlabel('Message Number (Oldest to Most Recent)')
    plt.plot(moving_averages)
    plt.savefig('foo.png')
    with open('foo.png', 'rb') as f:
      picture = discord.File(f)
      await msg.channel.send(file=picture)
    
  if "egative" in sentiment:
    #global count
    count += 1
  else:
    #global count
    count = 0
  if count >= 5:
    await msg.channel.send("A lot of negativity going around this discord server someone should send a happy picture!")
  if len(msg.attachments) > 0: #IMAGE SENT
      attachment = msg.attachments[0]
      print("HAS ATTACHMENT")
      if attachment.filename.endswith(".jpg") or attachment.filename.endswith(".jpeg") or attachment.filename.endswith(".png") or attachment.filename.endswith(".webp"):
          image = attachment.url
          response = requests.get(image)
          img = Image.open(BytesIO(response.content))
          np_img = np.asarray(img)
          grayscale = cv2.cvtColor(np_img, cv2.COLOR_BGR2GRAY) 
          if detection(grayscale, np_img):
            count = 0
            await msg.channel.send("Nice smile you little cutie! :)")
          else:
            await msg.channel.send("Hopefully this cutie can brighten your day up!")

  if msg.content == ">help":
    await msg.channel.send("Here's a list of the commands you can run with this bot:\n\tYou can enter '>help' for help.\n\tYou can enter '>getSent <word or phrase>' to see the sentimentality of your input.\n\tYou can enter '>trySent <word or phrase>' to see the single-instance sentimentality of an input.\n\tYou can enter '>vizSent' to graph the general sentimentality of the server as a function of time.\n\tYou can try out our experimental smile detection functionality. Upload and send a photo with the file formats .jpg, .jpeg, .png, or .webp to try it out!")
  if msg.content.startswith(">getSent "): #SENT DISCORD QUERY
    usedMessages = []
    input = msg.content[9:].lower()
    usedCounter = 0
    
    
    for message in messages[:]:
      if input in message:
        usedMessages.append(message)
        usedCounter += 1

    rawScore = 0

    for message in usedMessages:
      result = return_sentiment(message)
      print(result)
      if "ositive" in result:
        rawScore += 1
      elif "egative" in result:
        rawScore -= 1
      elif "eutral" in result:
        pass
      else:
        usedCounter -= 1
  
    if usedCounter <= 0:
      await msg.channel.send(f"There were no messages that include '{input}.' OR the algorithm had trouble finding relative sentiments.")

    else:
      total = float(rawScore) / float(usedCounter)
      sentAnswer = ""
      if total == 1.0:
        sentAnswer = "perfectly positive"
      elif total > 0.7:
        sentAnswer = "strongley positive"
      elif total > 0.3:
        sentAnswer = "somewhat positive"
      elif total > 0:
        sentAnswer = "slightly positive"
      elif total == 0:
        sentAnswer = "perfectly neutral"
      elif total == -1.0:
        sentAnswer = "perfectly negative"
      elif total < -0.7:
        sentAnswer = "strongly negative"
      elif total < -0.3:
        sentAnswer = "somewhat negative"
      else:
        sentAnswer = "slightly negative"
      await msg.channel.send(f"Calculating the average sentiment for {usedCounter} messages containing the phrase/keyword '{input}'...\nCalculated sentiment for phrases containing '{input}': {total}\nIn other words, the phrase '{input}' is {sentAnswer}.")

  if msg.content.startswith(">trySent "): #TRY DISCORD QUERY
    input = msg.content[9:]
    await msg.channel.send(return_sentiment(msg.content))

#Run on Discord
keep_alive()
client.run(os.getenv('TOKEN'))