import speech_recognition as sr
import pyttsx3
import datetime as dt
import pywhatkit as pk
import requests
import os
import pygame  # pygame for audio playback
import PyPDF2  # Updated PyPDF2 for PDF reading
import serial

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Initialize the recognizer and speaker
listener = sr.Recognizer()
speaker = pyttsx3.init()

# Set rate and voice
rate = speaker.getProperty('rate')
speaker.setProperty('rate', 130)
voices = speaker.getProperty('voices')
speaker.setProperty('voice', voices[1].id)  # Change index for different voices

# Your OpenWeatherMap API key
API_KEY = '3ec136d4c475adee4efe3c3219d70892'
WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather'

# Define wake-up word
va_name = 'atom'

# Initialize serial connection to Arduino
arduino = serial.Serial('COM5', 9600)  # Replace 'COM5' with the correct port

def speak(text):
    speaker.say(text)
    speaker.runAndWait()

def turn_led_on():
    arduino.write(b'0')  # Send '0' to Arduino to turn the LED on

def turn_led_off():
    arduino.write(b'1')  # Send '1' to Arduino to turn the LED off

def play_audio(file_path):
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        speak(f"Playing {os.path.basename(file_path)}")
        while pygame.mixer.music.get_busy():
            continue
    except Exception as e:
        print(f"An error occurred: {e}")
        speak("Sorry, I couldn't play the audio file.")

def read_pdf(file_path):
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                speaker.say(text)
                speaker.runAndWait()
    except Exception as e:
        print(f"An error occurred: {e}")
        speaker.say("Sorry, I couldn't read the PDF file.")
        speaker.runAndWait()

def get_weather(city):
    try:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'
        }
        response = requests.get(WEATHER_URL, params=params)
        data = response.json()

        if data['cod'] == 200:
            city_name = data['name']
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            report = f"The weather in {city_name} is currently {weather_desc} with a temperature of {temp} degrees Celsius."
            return report
        else:
            return "Sorry, I couldn't get the weather information for that location."
    except Exception as e:
        print(f'An error occurred while fetching weather information: {e}')
        return "Sorry, I couldn't get the weather information."

def get_duckduckgo_answer(query, word_limit=30):
    try:
        response = requests.get('https://api.duckduckgo.com/', params={
            'q': query,
            'format': 'json',
            'no_redirect': 1
        })
        data = response.json()
        answer = data.get('AbstractText', 'Sorry, I could not retrieve the information.')
        truncated_answer = ' '.join(answer.split()[:word_limit])

        if len(answer.split()) > word_limit:
            truncated_answer += '...'
        return truncated_answer
    except Exception as e:
        print(f'An error occurred: {e}')
        return 'Sorry, I could not retrieve the information.'

def take_command(idle_mode=True):
    command = ''
    try:
        with sr.Microphone() as source:
            if idle_mode:
                turn_led_on()  # Turn LED on when listening
                print('Waiting for wakeup word...')
                voice = listener.listen(source, timeout=2)
            else:
                turn_led_on()  # Turn LED on when listening
                print('Listening...')
                voice = listener.listen(source)

            command = listener.recognize_google(voice)
            command = command.lower()
            return command
    except sr.UnknownValueError:
        return ''
    except sr.RequestError:
        return ''
    except Exception as e:
        print(f'An error occurred: {e}')
        return ''
    finally:
        turn_led_off()  # Turn LED off when done listening

def listen_for_wakeup_word():
    while True:
        idle_command = take_command(idle_mode=True)
        if va_name in idle_command:
            print('Waking up...')
            speak(f'I am your {va_name}. How can I help you?')
            main()

def expand_query(query):
    query = query.lower()
    query = query.replace('who is ', '').replace('what is ', '').replace('which is ', '').replace('tell me about ', '')
    return query

def normalize_text(text):
    text = text.lower()
    text = text.replace('who is ', '').replace('what is ', '').replace('which is ', '').replace('tell me about ', '')
    return text

def main():
    audio_folder = r"C:\Users\edubotics\Desktop\music"
    pdf_folder = r"C:\Users\edubotics\Desktop\class"

    while True:
        user_command = take_command(idle_mode=False)
        if user_command:
            print(f"User command received: {user_command}")
            if 'stop' in user_command:
                speak('Going idle. Please call me with my name.')
                listen_for_wakeup_word()
            elif 'time' in user_command:
                cur_time = dt.datetime.now().strftime("%I:%M %p")
                print(cur_time)
                speak(cur_time)
            elif 'how' in user_command:
                speak('I am good. Thanks for asking.')
            elif 'search for' in user_command or 'google' in user_command:
                search_query = user_command.replace('search for ', '').replace('google ', '')
                print('Searching for ' + search_query)
                pk.search(search_query)
            elif 'who is' in user_command or 'which is' in user_command or 'what is' in user_command or 'tell me about' in user_command:
                query = normalize_text(user_command)
                detailed_query = expand_query(query)
                print(f'Searching DuckDuckGo for: {query}')
                info = get_duckduckgo_answer(detailed_query)
                print(f'Answer from DuckDuckGo: {info}')
                speak(info)
            elif 'weather in' in user_command:
                city = user_command.replace('weather in ', '')
                print(f'Fetching weather information for: {city}')
                weather_report = get_weather(city)
                print(weather_report)
                speak(weather_report)
            elif 'read pdf' in user_command:
                pdf_file_name = user_command.replace('read pdf ', '').strip() + ".pdf"
                pdf_path = os.path.join(pdf_folder, pdf_file_name)

                if os.path.exists(pdf_path):
                    print(f"Reading PDF file: {pdf_file_name}")
                    read_pdf(pdf_path)
                else:
                    speak(f"The file {pdf_file_name} does not exist in the class folder on the desktop.")
            elif 'play' in user_command:
                audio_file_name = user_command.replace('play ', '').strip() + ".mp3"
                audio_path = os.path.join(audio_folder, audio_file_name)

                if os.path.exists(audio_path):
                    print(f"Playing audio file: {audio_file_name}")
                    play_audio(audio_path)
                else:
                    speak(f"The file {audio_file_name} does not exist in the music folder on the desktop.")
            elif any(op in user_command for op in ['+', '-', '*', '/', 'times', 'x']):
                expression = user_command.replace('times', '').replace('multiplied by', '').replace('x', '*').replace(
                    'plus', '+').replace('minus', '-').replace('divided by', '/')
                try:
                    result = eval(expression)
                    print(f'Result: {result}')
                    speak(f'The result is {result}')
                except Exception as e:
                    print(f"Error in calculation: {e}")
                    speak("Sorry, I couldn't calculate that.")
            # New Commands for Arduino Actions
            elif 'shake hand' in user_command:
                print("Shaking hand")
                arduino.write(b'3')
                speak("Shaking hand.")
            elif 'walk' in user_command:
                print("Walking")
                arduino.write(b'4')
                speak("Walking.")
            elif 'left' in user_command:
                print("Turning left")
                arduino.write(b'5')
                speak("Turning left.")
            elif 'right' in user_command:
                print("Turning right")
                arduino.write(b'6')
                speak("Turning right.")
            elif 'back' in user_command:
                print("Moving back")
                arduino.write(b'7')
                speak("Moving back.")
            else:
                speak('Sorry, I did not understand that command.')

if __name__ == '__main__':
    speak(f'Hello! My name is {va_name}.')
    listen_for_wakeup_word()