import serial
import threading

port = "COM3"
baudrate = 115200

running = True


def reader(ser):
    while running:
        try:
            if ser.in_waiting > 0:
                data = ser.readline().decode('ascii').strip()
                print("Arduino:", data)
        except Exception as e:
            print('Ошибка считывания', e)


def writer(ser):
    global running
    while running:
        try:
            cmd = input("Command: ")
            if cmd.lower() == 'exit':
                running = False
                break
            ser.write(cmd.encode())
        except:
            break


try:
    ser = serial.Serial(port, baudrate)
    print("Connected to Arduino")

    # Запускаем потоки
    threading.Thread(target=reader, args=(ser,), daemon=True).start()
    writer(ser)  # Основной поток становится потоком отправки

except Exception as e:
    print("Error:", e)
finally:
    running = False
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Disconnected")
