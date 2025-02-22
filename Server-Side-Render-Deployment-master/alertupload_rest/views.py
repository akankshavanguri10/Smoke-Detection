from alertupload_rest.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
#from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.core.mail import send_mail
import re
from threading import Thread
from twilio.rest import Client
from django.conf import settings



def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

@api_view(['POST'])
#@permission_classes((IsAuthenticated, ))
def post_alert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        identify_email_sms(serializer)

    else:
        return JsonResponse({'error':'Unable to process data!'},status=400)

    return Response(request.META.get('HTTP_AUTHORIZATION'))

def identify_email_sms(serializer):

    if(re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', serializer.data['alert_receiver'])):  
        print("Valid Email")
        send_email(serializer)
    elif re.compile("[+91][0-9]{10}").match(serializer.data['alert_receiver']):
        # 1) Begins with +3706
        # 2) Then contains 7 digits 
        print("Valid Mobile Number")
        send_sms(serializer)
    else:
        print("Invalid Email or Mobile number")

@start_new_thread
def send_email(serializer):
    send_mail('Weapon Detected!', 
    prepare_alert_message(serializer), 
    'weapondetectionsystemproject@gmail.com',
    [serializer.data['alert_receiver']],
    fail_silently=True,)

@start_new_thread
def send_sms(serializer):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(body=prepare_alert_message(serializer),
                                    from_=settings.TWILIO_NUMBER,
                                    to=serializer.data['alert_receiver'])


def prepare_alert_message(serializer):
    image_data= split(serializer.data['image'], ".")
    uuid=image_data[0]
    url='http://127.0.0.1:8000/alert' + uuid

    return 'Smoke Detected! View alert at ' + url

def split(value, key):
    return str(value).split(key)