from ib_insync import *
import time

# Try different client IDs
client_ids = [1, 2, 3, 100, 999]

for client_id in client_ids:
    print(f"\n🔌 Trying client ID: {client_id}")
    
    try:
        ib = IB()
        print(f"   Connecting to 127.0.0.1:4001 with clientId={client_id}...")
        
        # Try to connect with a shorter timeout
        ib.connect('127.0.0.1', 4001, clientId=client_id, timeout=10)
        
        if ib.isConnected():
            print(f"   ✅ Connected successfully with clientId={client_id}!")
            
            # Try to get some basic info
            try:
                print("   📊 Getting account info...")
                accounts = ib.managedAccounts()
                if accounts:
                    print(f"   ✅ Found accounts: {accounts}")
                else:
                    print("   ⚠️  No accounts found")
            except Exception as e:
                print(f"   ⚠️  Could not get account info: {e}")
            
            ib.disconnect()
            print(f"   🔌 Disconnected from clientId={client_id}")
            break
        else:
            print(f"   ❌ Failed to connect with clientId={client_id}")
            ib.disconnect()
            
    except Exception as e:
        print(f"   ❌ Error with clientId={client_id}: {e}")
        try:
            ib.disconnect()
        except:
            pass
    
    time.sleep(1)  # Wait a bit between attempts

print("\n🏁 Connection test completed!")
