#!/bin/bash
set -eu
IN=$1; OUT=$2; MIN=$3
R=$PWD/report.txt; : > $R
rm -rf w && mkdir w && cd w && unzip -q ../$IN
APP=$(ls -d Payload/*.app)
# Info.plist minimums
find Payload -name Info.plist | while read p; do
  if /usr/libexec/PlistBuddy -c 'Print :MinimumOSVersion' "$p" >/dev/null 2>&1; then
    echo "plist $p: $(/usr/libexec/PlistBuddy -c 'Print :MinimumOSVersion' "$p") -> $MIN" >> $R
    /usr/libexec/PlistBuddy -c "Set :MinimumOSVersion $MIN" "$p"
  fi
done
SDK=$(xcrun --sdk iphoneos --show-sdk-path)
# collect Mach-Os
find Payload -type f | while read f; do file -b "$f" | grep -q Mach-O && echo "$f" || true; done > ../machos.txt
while read f; do
  ent=$(mktemp); codesign -d --entitlements :- "$f" > "$ent" 2>/dev/null || true
  echo "$f" >> ../ents.txt; [ -s "$ent" ] && cp "$ent" "$f.ent.plist.tmp"
  echo "== $f: $(vtool -show-build "$f" 2>/dev/null | grep -E 'minos|sdk' | tr -s ' ' | tr '\n' ' ')" >> $R
  codesign --remove-signature "$f" 2>/dev/null || true
  vtool -set-build-version ios $MIN 27.0 -replace -output "$f.new" "$f" && mv "$f.new" "$f"
done < ../machos.txt
python3 ../weaken.py "$APP/Andarium" '_$s7SwiftUI12TupleContentVyxxQp_QPGAA07ToolbarD0AARvzAaERzlMc' '_$s7SwiftUI13PreferenceKeyP22_preferenceValuesEqualySb5ValueQz_AFtFZTq' '_$s7SwiftUI13PreferenceKeyPAASQ5ValueRpzrlE22_preferenceValuesEqualySbAE_AEtFZ' >> $R
RB="_AVAudioSessionDidBecomeInactiveNotification=_AVAudioSessionInterruptionNotification _AVAudioSessionResumptionRecommendationNotification=_AVAudioSessionInterruptionNotification"
for f in $APP/Frameworks/KRuntime_*/KRuntime_*; do python3 ../weaken.py "$f" _AVAudioSessionDeactivationContextKey _AVAudioSessionResumptionContextKey >> $R; python3 ../rebind.py "$f" $RB >> $R; done
# symbol check against iOS SDK tbds
echo "### SDK $(xcrun --sdk iphoneos --show-sdk-version)" >> $R
python3 ../symcheck.py "$SDK" ../machos.txt >> $R 2>&1 || true
# ad-hoc re-sign, inner first
tac ../machos.txt | while read f; do
  e="$f.ent.plist.tmp"
  if [ -f "$e" ]; then codesign -f -s - --entitlements "$e" "$f" >/dev/null 2>&1 || codesign -f -s - "$f" || true; rm -f "$e"
  else codesign -f -s - "$f" >/dev/null 2>&1 || true; fi
done
find Payload -name '*.ent.plist.tmp' -delete
for b in $(find Payload -depth -name '*.framework' -o -depth -name '*.appex'); do codesign -f -s - "$b" >/dev/null 2>&1 || true; done
codesign -f -s - --entitlements <(codesign -d --entitlements :- "$APP" 2>/dev/null || echo '<plist/>') "$APP" >/dev/null 2>&1 || true
zip -qry ../$OUT Payload
cat $R | head -300
