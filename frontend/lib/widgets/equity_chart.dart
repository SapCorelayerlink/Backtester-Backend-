import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../models/strategy_models.dart';

class EquityChart extends StatelessWidget {
  final List<EquityPoint> equityPoints;

  const EquityChart({super.key, required this.equityPoints});

  @override
  Widget build(BuildContext context) {
    if (equityPoints.isEmpty) {
      return const Center(
        child: Text('No equity data available'),
      );
    }

    // Convert timestamp strings to DateTime objects and create chart data
    final chartData = equityPoints.asMap().entries.map((entry) {
      final index = entry.key;
      final point = entry.value;
      
      return FlSpot(index.toDouble(), point.equity);
    }).toList();

    // Find min and max values for better chart scaling
    final minEquity = equityPoints.map((p) => p.equity).reduce((a, b) => a < b ? a : b);
    final maxEquity = equityPoints.map((p) => p.equity).reduce((a, b) => a > b ? a : b);
    final equityRange = maxEquity - minEquity;
    final padding = equityRange * 0.1; // 10% padding

    // Calculate safe intervals to prevent zero values
    final bottomInterval = (equityPoints.length / 5).ceil().toDouble();
    final leftInterval = (equityRange / 5).ceil().toDouble();
    
    // Ensure minimum intervals to prevent fl_chart assertion errors
    final safeBottomInterval = bottomInterval > 0 ? bottomInterval : 1.0;
    final safeLeftInterval = leftInterval > 0 ? leftInterval : 1.0;

    return LineChart(
      LineChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: true,
          horizontalInterval: safeLeftInterval,
          verticalInterval: safeBottomInterval,
          getDrawingHorizontalLine: (value) {
            return FlLine(
              color: Colors.grey[300]!,
              strokeWidth: 1,
            );
          },
          getDrawingVerticalLine: (value) {
            return FlLine(
              color: Colors.grey[300]!,
              strokeWidth: 1,
            );
          },
        ),
        titlesData: FlTitlesData(
          show: true,
          rightTitles: AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
          topTitles: AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              interval: safeBottomInterval,
              getTitlesWidget: (value, meta) {
                if (value.toInt() >= equityPoints.length) return const Text('');
                
                final point = equityPoints[value.toInt()];
                final dateTime = DateTime.tryParse(point.timestamp);
                if (dateTime == null) return const Text('');
                
                return Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(
                    DateFormat('MM/dd').format(dateTime),
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              interval: safeLeftInterval,
              getTitlesWidget: (value, meta) {
                return Text(
                  NumberFormat.compact().format(value),
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                );
              },
              reservedSize: 60,
            ),
          ),
        ),
        borderData: FlBorderData(
          show: true,
          border: Border.all(color: Colors.grey[400]!),
        ),
        minX: 0,
        maxX: (equityPoints.length - 1).toDouble(),
        minY: minEquity - padding,
        maxY: maxEquity + padding,
        lineBarsData: [
          LineChartBarData(
            spots: chartData,
            isCurved: true,
            gradient: LinearGradient(
              colors: [
                Colors.blue[400]!,
                Colors.blue[600]!,
              ],
            ),
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: false,
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                colors: [
                  Colors.blue[400]!.withValues(alpha: 0.3),
                  Colors.blue[600]!.withValues(alpha: 0.1),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
        ],
        lineTouchData: LineTouchData(
          enabled: true,
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((touchedSpot) {
                final index = touchedSpot.x.toInt();
                if (index >= equityPoints.length) return null;
                
                final point = equityPoints[index];
                final dateTime = DateTime.tryParse(point.timestamp);
                final dateStr = dateTime != null 
                    ? DateFormat('MM/dd HH:mm').format(dateTime)
                    : point.timestamp;
                
                return LineTooltipItem(
                  '$dateStr\n\$${point.equity.toStringAsFixed(2)}',
                  const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                );
              }).toList();
            },
          ),
        ),
      ),
    );
  }
}
