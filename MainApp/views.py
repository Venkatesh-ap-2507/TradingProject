from django.shortcuts import render
from django.conf import settings
import os
import csv
import json
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from MainApp.models import Candle


def handle_upload_file(file, timeframe):
    candles = []
    file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    with open(file_path, 'wb+') as f:
        for chunk in file.chunks():
            f.write(chunk)

    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                date_str = row.get('DATE')
                time_str = row.get('TIME')
                if date_str and time_str:
                    timestamp_str = f"{date_str} {time_str}"
                    timestamp = datetime.strptime(
                        timestamp_str, '%Y%m%d %H:%M')

                    candle = Candle(
                        timestamp=timestamp,
                        open=float(row.get('OPEN')),
                        high=float(row.get('HIGH')),
                        low=float(row.get('LOW')),
                        close=float(row.get('CLOSE'))
                    )
                    candle.save()
                    candles.append({
                        "id": candle.id,
                        "open": candle.open,
                        "high": candle.high,
                        "low": candle.low,
                        "close": candle.close,
                        "date": candle.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    })
            except Exception as e:
                print(f"Error processing row: {e}")

    converted_candles = convert_to_timeframe(candles, int(timeframe))
    json_file_path = os.path.join(
        settings.MEDIA_ROOT, 'converted_candles.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(converted_candles, json_file, default=str)

    return json_file_path


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


def convert_to_timeframe(candles, timeframe):
    grouped_candles = []
    current_timeframe_candles = [candles[0]]
    current_timeframe_start = datetime.strptime(
        candles[0]['date'], '%Y-%m-%d %H:%M:%S')

    for candle in candles[1:]:
        candle_date = datetime.strptime(candle['date'], '%Y-%m-%d %H:%M:%S')
        if (candle_date - current_timeframe_start).total_seconds() < timeframe * 60:
            current_timeframe_candles.append(candle)
        else:
            grouped_candles.append(
                calculate_timeframe_stats(current_timeframe_candles))
            current_timeframe_candles = [candle]
            current_timeframe_start = candle_date

    grouped_candles.append(
        calculate_timeframe_stats(current_timeframe_candles))

    return grouped_candles


def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        timeframe = request.POST.get('timeframe')

        if file and timeframe:
            json_file_path = handle_upload_file(file, timeframe)
            with open(json_file_path, 'rb') as f:
                response = HttpResponse(
                    f.read(), content_type='application/json')
                response[
                    'Content-Disposition'] = f'attachment; filename="{os.path.basename(json_file_path)}"'
                return response
        else:
            return JsonResponse({'error': 'Missing file or timeframe'}, status=400)

    return render(request, 'MainApp/upload.html')
