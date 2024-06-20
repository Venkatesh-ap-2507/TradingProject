from django.shortcuts import render
from django.conf import settings
import os,csv,json
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from MainApp.models import Candle

# Create your views here.

def handle_upload_file(file,timeframe):
    candles=[]
    file_path  = os.path.join(settings.MEDIA_ROOT,file.name)
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    with open(file_path, 'wb+') as f:
        for chunk in file.chunks():
            f.write(chunk)
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames
        print("CSV Headers:", headers)

        first_row = next(reader)
        print("First Row:", first_row)
        for row in reader:
            print(row)  # Check the contents of each row
            timestamp = f"{row['DATE']} {row['TIME']}"

            # timestamp = datetime.strptime(timestamp_str, '%Y%m%d %H:%M')
            candle = Candle(
                timestamp=timestamp, 
                open=float(row['OPEN']),
                high=float(row['HIGH']),
                low=float(row['LOW']),
                close=float(row['CLOSE'])
            ) 
            # candles.append(candle)
            candle.save()
            candles.append({
                "id": candle.id,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "date": candle.date
            })
            converted_candles = convert_to_timeframe(candles,int(timeframe))

            json_file_p = os.path.join(settings.MEDIA_ROOT,'converted_candles.json')
            with open(json_file_p, 'w') as json_file:
                json.dump(converted_candles, json_file,default=str) #descerilaiztion 
                
            return json_file_p


def calculate_timeframe_stats(candles):
    open_price = candles[0]['open']
    close_price = candles[-1]['close']
    high_price = max(c['high'] for c in candles)
    low_price = min(c['low'] for c in candles)
    date = candles[-1]['date']
    return {
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "date": date
    }

def convert_to_timeframe(candles,timeframe):
    grouped_candles = []
    current_timeframe_candles=[]
    current_timeframe_start = candles[0]['date']
    
    for candle in candles:
        if (candle['date'] - current_timeframe_start).total_seconds() < timeframe * 60:
            current_timeframe_candles.append(candle)
        else:
            if current_timeframe_candles:

                grouped_candles.append(calculate_timeframe_stats(current_timeframe_candles))
            current_timeframe_candles = [candle]
            current_timeframe_start = candle['date']

    if current_timeframe_candles:
        grouped_candles.append(calculate_timeframe_stats(current_timeframe_candles))

    return grouped_candles       


def upload_file(request):
    if request.method == 'POST':
        file = request.FILES['file']
        timeframe = request.POST.get('timeframe')
        if file and timeframe:
            json_file_path = handle_upload_file(file, timeframe)
            response = HttpResponse(open(json_file_path,'rb'),content_type='application/json')
            response[
                'Content-Disposition'] = f'attachment; filename="{os.path.basename(json_file_path)}"'
            return response
        else:
            return JsonResponse({'error': 'Missing file or timeframe'}, status=400)
    return render(request, 'MainApp/upload.html')
        
    
        

