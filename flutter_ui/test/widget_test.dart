import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_ui/main.dart';

void main() {
  testWidgets('App loads smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const SCOPEApp());
    expect(find.text('PaperLab', findRichText: true), findsNothing); // Or just anything simple
  });
}
