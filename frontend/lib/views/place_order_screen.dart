import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/broker_provider.dart';
import '../models/broker_models.dart';

class PlaceOrderScreen extends StatefulWidget {
  const PlaceOrderScreen({super.key});

  @override
  State<PlaceOrderScreen> createState() => _PlaceOrderScreenState();
}

class _PlaceOrderScreenState extends State<PlaceOrderScreen> {
  final _formKey = GlobalKey<FormState>();
  final _symbolController = TextEditingController(text: 'AAPL');
  final _qtyController = TextEditingController(text: '10');
  String _selectedSide = 'buy';
  String _selectedType = 'market';

  @override
  void dispose() {
    _symbolController.dispose();
    _qtyController.dispose();
    super.dispose();
  }

  Future<void> _placeOrder() async {
    if (!_formKey.currentState!.validate()) return;

    final brokerProvider = context.read<BrokerProvider>();
    
    final request = OrderRequest(
      symbol: _symbolController.text,
      qty: double.parse(_qtyController.text),
      side: _selectedSide,
      type: _selectedType,
    );

    await brokerProvider.placeOrder('paper', request);

    if (brokerProvider.error.isEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Order placed successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        // Clear form
        _formKey.currentState!.reset();
        _symbolController.text = 'AAPL';
        _qtyController.text = '10';
        _selectedSide = 'buy';
        _selectedType = 'market';
        setState(() {});
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<BrokerProvider>(
        builder: (context, brokerProvider, child) {
          return Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Place Order',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _symbolController,
                          decoration: const InputDecoration(
                            labelText: 'Symbol',
                            border: OutlineInputBorder(),
                            hintText: 'e.g., AAPL, MSFT, GOOGL',
                          ),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a symbol';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _qtyController,
                          decoration: const InputDecoration(
                            labelText: 'Quantity',
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.number,
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter quantity';
                            }
                            if (double.tryParse(value) == null) {
                              return 'Please enter a valid number';
                            }
                            if (double.parse(value) <= 0) {
                              return 'Quantity must be greater than 0';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          value: _selectedSide,
                          decoration: const InputDecoration(
                            labelText: 'Side',
                            border: OutlineInputBorder(),
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'buy',
                              child: Text('Buy'),
                            ),
                            DropdownMenuItem(
                              value: 'sell',
                              child: Text('Sell'),
                            ),
                          ],
                          onChanged: (value) {
                            setState(() {
                              _selectedSide = value!;
                            });
                          },
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          value: _selectedType,
                          decoration: const InputDecoration(
                            labelText: 'Order Type',
                            border: OutlineInputBorder(),
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'market',
                              child: Text('Market'),
                            ),
                            DropdownMenuItem(
                              value: 'limit',
                              child: Text('Limit'),
                            ),
                          ],
                          onChanged: (value) {
                            setState(() {
                              _selectedType = value!;
                            });
                          },
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                
                // Order Summary
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Order Summary',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 16),
                        _OrderSummaryRow(
                          label: 'Symbol',
                          value: _symbolController.text.isEmpty ? '-' : _symbolController.text,
                        ),
                        const SizedBox(height: 8),
                        _OrderSummaryRow(
                          label: 'Side',
                          value: _selectedSide.toUpperCase(),
                          color: _selectedSide == 'buy' ? Colors.green : Colors.red,
                        ),
                        const SizedBox(height: 8),
                        _OrderSummaryRow(
                          label: 'Quantity',
                          value: _qtyController.text.isEmpty ? '-' : _qtyController.text,
                        ),
                        const SizedBox(height: 8),
                        _OrderSummaryRow(
                          label: 'Type',
                          value: _selectedType.toUpperCase(),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Error Display
                if (brokerProvider.error.isNotEmpty)
                  Card(
                    color: Colors.red[50],
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline, color: Colors.red[700]),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              brokerProvider.error,
                              style: TextStyle(color: Colors.red[700]),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                const SizedBox(height: 16),

                // Place Order Button
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: brokerProvider.isLoading ? null : _placeOrder,
                    child: brokerProvider.isLoading
                        ? const CircularProgressIndicator()
                        : const Text('Place Order'),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _OrderSummaryRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;

  const _OrderSummaryRow({
    required this.label,
    required this.value,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Colors.grey[600],
          ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
