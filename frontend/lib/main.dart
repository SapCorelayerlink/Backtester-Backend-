import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import 'providers/api_provider.dart';
import 'providers/strategy_provider.dart';
import 'providers/broker_provider.dart';
import 'views/home_screen.dart';

void main() {
  runApp(const BactesterApp());
}

class BactesterApp extends StatelessWidget {
  const BactesterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ApiProvider()),
        ChangeNotifierProvider(create: (_) => StrategyProvider()),
        ChangeNotifierProvider(create: (_) => BrokerProvider()),
      ],
      child: MaterialApp(
        title: 'Bactester Trading',
        theme: _buildAppleLikeTheme(),
        home: const HomeScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }

  ThemeData _buildAppleLikeTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,

      // Color Scheme - Apple-like soft colors
      colorScheme: const ColorScheme.light(
        primary: Color(0xFF007AFF), // Apple Blue
        secondary: Color(0xFF5856D6), // Apple Purple
        surface: Color(0xFFF2F2F7), // Apple Light Gray
        background: Color(0xFFFFFFFF), // Pure White
        onPrimary: Color(0xFFFFFFFF), // White text on primary
        onSecondary: Color(0xFFFFFFFF), // White text on secondary
        onSurface: Color(0xFF1C1C1E), // Dark text on surface
        onBackground: Color(0xFF1C1C1E), // Dark text on background
        error: Color(0xFFFF3B30), // Apple Red
        onError: Color(0xFFFFFFFF), // White text on error
        outline: Color(0xFFC7C7CC), // Apple Border Gray
        outlineVariant: Color(0xFFE5E5EA), // Apple Light Border
      ),

      // App Bar Theme - Clean and minimal
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFFF2F2F7),
        foregroundColor: Color(0xFF1C1C1E),
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: Color(0xFF1C1C1E),
          fontSize: 17,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.4,
        ),
        iconTheme: IconThemeData(
          color: Color(0xFF007AFF),
          size: 24,
        ),
      ),

      // Card Theme - Rounded corners with subtle shadows
      cardTheme: CardThemeData(
        elevation: 0,
        shadowColor: const Color(0xFF000000).withOpacity(0.1),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        color: const Color(0xFFFFFFFF),
        surfaceTintColor: Colors.transparent,
      ),

      // Elevated Button Theme - Apple-style buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF007AFF),
          foregroundColor: const Color(0xFFFFFFFF),
          elevation: 0,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          textStyle: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.4,
          ),
        ),
      ),

      // Text Button Theme
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: const Color(0xFF007AFF),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          textStyle: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.4,
          ),
        ),
      ),

      // Outlined Button Theme
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF007AFF),
          side: const BorderSide(color: Color(0xFF007AFF), width: 1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          textStyle: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.4,
          ),
        ),
      ),

      // Input Decoration Theme - Clean text fields
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF2F2F7),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF007AFF), width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFFF3B30), width: 1),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        labelStyle: const TextStyle(
          color: Color(0xFF8E8E93),
          fontSize: 17,
          fontWeight: FontWeight.w400,
        ),
        hintStyle: const TextStyle(
          color: Color(0xFF8E8E93),
          fontSize: 17,
          fontWeight: FontWeight.w400,
        ),
      ),

      // Text Theme - Apple-style typography
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontSize: 34,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.8,
          color: Color(0xFF1C1C1E),
        ),
        displayMedium: TextStyle(
          fontSize: 28,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.6,
          color: Color(0xFF1C1C1E),
        ),
        displaySmall: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.4,
          color: Color(0xFF1C1C1E),
        ),
        headlineLarge: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.4,
          color: Color(0xFF1C1C1E),
        ),
        headlineMedium: TextStyle(
          fontSize: 17,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.4,
          color: Color(0xFF1C1C1E),
        ),
        headlineSmall: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
          color: Color(0xFF1C1C1E),
        ),
        titleLarge: TextStyle(
          fontSize: 17,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.4,
          color: Color(0xFF1C1C1E),
        ),
        titleMedium: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
          color: Color(0xFF1C1C1E),
        ),
        titleSmall: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
          color: Color(0xFF1C1C1E),
        ),
        bodyLarge: TextStyle(
          fontSize: 17,
          fontWeight: FontWeight.w400,
          letterSpacing: -0.4,
          color: Color(0xFF1C1C1E),
        ),
        bodyMedium: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w400,
          letterSpacing: -0.2,
          color: Color(0xFF1C1C1E),
        ),
        bodySmall: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w400,
          letterSpacing: -0.2,
          color: Color(0xFF8E8E93),
        ),
        labelLarge: TextStyle(
          fontSize: 17,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.4,
          color: Color(0xFF007AFF),
        ),
        labelMedium: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
          color: Color(0xFF007AFF),
        ),
        labelSmall: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
          color: Color(0xFF007AFF),
        ),
      ),

      // Icon Theme
      iconTheme: const IconThemeData(
        color: Color(0xFF007AFF),
        size: 24,
      ),

      // Divider Theme
      dividerTheme: const DividerThemeData(
        color: Color(0xFFE5E5EA),
        thickness: 0.5,
        space: 1,
      ),

      // Scaffold Background
      scaffoldBackgroundColor: const Color(0xFFF2F2F7),

      // Page Transitions
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.android: CupertinoPageTransitionsBuilder(),
          TargetPlatform.windows: CupertinoPageTransitionsBuilder(),
          TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.linux: CupertinoPageTransitionsBuilder(),
        },
      ),
    );
  }
}
