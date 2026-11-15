/*
 * TorchOS Sidecar v0.1 — ESP32-WROOM-32 companion for the BlackBerry Torch 9810.
 *
 * Classic Bluetooth SPP (the Torch speaks JSR-82 btspp) + USB serial mirror.
 * Line protocol, ASCII, '\n' terminated, max 96 chars in:
 *   PING            -> PONG
 *   INFO            -> INFO TorchOS-Sidecar 0.1 chip=<model> rev=<n> heap=<bytes> up=<s> rfid=<ok|absent>
 *   HELP            -> HELP <commands>
 *   RFID ON|OFF     -> OK RFID ON|OFF   (scan loop; events below)
 *   RFID ONCE       -> RFID <uid-hex> <type> | RFID NONE (waits up to 3 s)
 * Events while scanning:  RFID <uid-hex> <type>
 * Errors:                 ERR <reason>
 *
 * Read-only by design: no GPIO writes, relays, CAN transmit or OTA in v0.1.
 * Bluetooth pairing is "Just Works" (no PIN), so anyone in range could read UIDs
 * while it is discoverable. An authenticated channel must come before any actuator.
 *
 * RC522 wiring (VSPI): SDA/SS=GPIO5, SCK=18, MOSI=23, MISO=19, RST=22, 3.3V, GND.
 * NEVER power the RC522 from 5V.
 */
#include <BluetoothSerial.h>
#include <SPI.h>
#include <MFRC522.h>

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error "Classic Bluetooth required (ESP32-WROOM-32, not S2/S3/C3)"
#endif

static const char *NAME = "TorchOS-Sidecar";
static const char *VERSION = "0.1";
static const uint8_t SIDECAR_SS_GPIO = 5, SIDECAR_RST_GPIO = 22;
static const size_t LINE_MAX = 96;

BluetoothSerial bt;
MFRC522 rfid(SIDECAR_SS_GPIO, SIDECAR_RST_GPIO);
bool rfidPresent = false, scanning = false;
String btLine, usbLine;
String lastUid;
unsigned long lastUidAt = 0;

void emit(const String &s) {
  Serial.println(s);
  if (bt.hasClient()) bt.println(s);
}

bool detectRfid() {
  byte v = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  return v == 0x91 || v == 0x92 || v == 0x88 || v == 0x12;  // genuine + common clones
}

String uidHex() {
  String s;
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) s += '0';
    s += String(rfid.uid.uidByte[i], HEX);
  }
  s.toUpperCase();
  return s;
}

String cardType() {
  String t = rfid.PICC_GetTypeName(rfid.PICC_GetType(rfid.uid.sak));
  t.replace(' ', '_');
  return t;
}

bool readCard(String &uid, String &type) {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return false;
  uid = uidHex();
  type = cardType();
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  return true;
}

void handle(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  String up = cmd;
  up.toUpperCase();
  if (up == "PING") emit("PONG");
  else if (up == "HELP") emit("HELP PING INFO HELP RFID_ON RFID_OFF RFID_ONCE (use spaces: RFID ON)");
  else if (up == "INFO") {
    emit(String("INFO ") + NAME + " " + VERSION + " chip=" + ESP.getChipModel() + " rev=" + ESP.getChipRevision() +
         " heap=" + ESP.getFreeHeap() + " up=" + (millis() / 1000) + " rfid=" + (rfidPresent ? "ok" : "absent"));
  } else if (up == "RFID ON" || up == "RFID OFF") {
    if (!rfidPresent) { emit("ERR RFID reader not detected (check wiring, 3.3V)"); return; }
    scanning = (up == "RFID ON");
    emit(String("OK RFID ") + (scanning ? "ON" : "OFF"));
  } else if (up == "RFID ONCE") {
    if (!rfidPresent) { emit("ERR RFID reader not detected (check wiring, 3.3V)"); return; }
    String uid, type;
    unsigned long until = millis() + 3000;
    while (millis() < until) {
      if (readCard(uid, type)) { emit("RFID " + uid + " " + type); return; }
      delay(50);
    }
    emit("RFID NONE");
  } else emit("ERR unknown command (try HELP)");
}

void pump(Stream &s, String &buf) {
  while (s.available()) {
    char c = (char)s.read();
    if (c == '\n' || c == '\r') { handle(buf); buf = ""; }
    else if (c >= 0x20 && c <= 0x7E) {
      if (buf.length() < LINE_MAX) buf += c;
      else { buf = ""; emit("ERR line too long"); }
    }
  }
}

void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();
  delay(50);
  rfidPresent = detectRfid();
  bt.begin(NAME);
  emit(String("READY ") + NAME + " " + VERSION + " rfid=" + (rfidPresent ? "ok" : "absent"));
}

void loop() {
  pump(Serial, usbLine);
  pump(bt, btLine);
  if (scanning) {
    String uid, type;
    if (readCard(uid, type)) {
      if (uid != lastUid || millis() - lastUidAt > 2000) emit("RFID " + uid + " " + type);  // debounce
      lastUid = uid;
      lastUidAt = millis();
    }
  }
  delay(10);
}
