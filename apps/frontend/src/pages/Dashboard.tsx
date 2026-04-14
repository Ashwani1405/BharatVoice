import React, { useEffect, useState } from 'react';
import client from '../api/client';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

declare global {
  interface Window {
    Razorpay?: any;
  }
}

const RAZORPAY_KEY_ID = import.meta.env.VITE_RAZORPAY_KEY_ID || 'rzp_test_SdIBcBnjZbPuwU';

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      return resolve(true);
    }

    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => reject(false);
    document.body.appendChild(script);
  });
}

export default function Dashboard() {
  const [amount, setAmount] = useState(10000);
  const [message, setMessage] = useState('');
  const [orderId, setOrderId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState<Array<any>>([]);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      localStorage.setItem('auth_token', 'dev_token');
    }

    fetchWallet();
    fetchTransactions();
  }, []);

  const fetchWallet = async () => {
    try {
      const response = await client.get('/payments/wallet');
      setBalance(response.data.balance ?? 0);
    } catch (error) {
      console.error('Failed to fetch wallet', error);
    }
  };

  const fetchTransactions = async () => {
    try {
      const response = await client.get('/payments/transactions');
      setTransactions(response.data.transactions ?? []);
    } catch (error) {
      console.error('Failed to fetch transactions', error);
    }
  };

  const confirmPayment = async (paymentResult: any) => {
    try {
      setMessage('Recording payment in the ledger...');
      await client.post('/payments/confirm-payment', {
        payment_id: paymentResult.razorpay_payment_id,
        amount,
        description: 'Razorpay wallet top-up',
      });

      await fetchWallet();
      await fetchTransactions();
      setMessage(`Top-up recorded: ${paymentResult.razorpay_payment_id}`);
    } catch (error: any) {
      console.error('Failed to record payment', error);
      setMessage('Payment was successful, but ledger update failed.');
    }
  };

  const handleTopUp = async () => {
    setIsLoading(true);
    setMessage('Preparing Razorpay checkout...');

    try {
      await loadRazorpayScript();

      const response = await client.post('/payments/create-order', {}, {
        params: { amount },
      });

      const order = response.data;
      const orderIdValue = order?.order_id;

      if (!orderIdValue) {
        throw new Error('Order ID not returned by backend');
      }

      setOrderId(orderIdValue);
      setMessage('Order created. Opening Razorpay payment window...');

      const options = {
        key: RAZORPAY_KEY_ID,
        amount,
        currency: 'INR',
        order_id: orderIdValue,
        name: 'BharatVoice',
        description: 'Wallet top-up',
        handler: function (paymentResult: any) {
          confirmPayment(paymentResult);
        },
        modal: {
          ondismiss: function () {
            setMessage('Payment window closed before completion.');
          },
        },
        prefill: {
          name: 'BharatVoice User',
          email: 'user@example.com',
          contact: '',
        },
        notes: {
          backend_order_id: orderIdValue,
        },
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (error: any) {
      console.error('Payment error:', error);
      setMessage(error?.message || 'Failed to start payment.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 mt-10 space-y-8">
      <div className="grid gap-8 lg:grid-cols-[1.4fr_0.9fr]">
        <Card>
          <div className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold">Your Wallet</h1>
                <p className="text-slate-400 mt-2">
                  Top up your wallet with Razorpay and view your balance and transaction history.
                </p>
              </div>
              <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-sm text-emerald-300">
                Connected
              </span>
            </div>

            <div className="grid gap-4 md:grid-cols-[1.1fr_0.9fr]">
              <div className="space-y-4">
                <label className="block text-sm font-medium text-slate-300">Amount (INR)</label>
                <input
                  type="number"
                  min={1}
                  value={Math.max(1, amount / 100)}
                  onChange={(event) => setAmount(Math.max(1, Number(event.target.value)) * 100)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none focus:border-fintech-primary"
                />
              </div>
              <div className="flex items-end">
                <Button onClick={handleTopUp} disabled={isLoading} className="w-full py-4">
                  {isLoading ? 'Starting payment...' : 'Top up wallet'}
                </Button>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-700 bg-slate-950/60 p-6 text-sm text-slate-300">
              <p className="text-slate-400">Current balance</p>
              <p className="text-4xl font-bold text-white">₹{(balance / 100).toFixed(2)}</p>
              <p className="mt-3 text-slate-500">Your wallet balance is backed by the ledger service.</p>
            </div>

            <div className="space-y-3 rounded-2xl border border-slate-700 bg-slate-950/60 p-4 text-sm text-slate-300">
              <div>
                <p className="font-semibold text-white">Backend payment status</p>
                <p>{message || 'Create an order to begin the Razorpay checkout flow.'}</p>
              </div>
              {orderId ? (
                <div className="rounded-lg bg-slate-900 p-3 text-xs text-slate-400">
                  Order ID: {orderId}
                </div>
              ) : null}
            </div>
          </div>
        </Card>

        <Card className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold">Recent transactions</h2>
            <p className="text-slate-400 mt-2">
              Your recorded top-ups and ledger entries appear here.
            </p>
          </div>

          <div className="space-y-3">
            {transactions.length === 0 ? (
              <div className="rounded-2xl border border-slate-700 bg-slate-950/60 p-6 text-slate-400">
                No transactions yet. Top up your wallet to generate ledger entries.
              </div>
            ) : (
              transactions.map((tx) => (
                <div key={tx.id} className="rounded-2xl border border-slate-700 bg-slate-950/60 p-4 text-sm">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-white">{tx.type === 'credit' ? 'Wallet top-up' : 'Debit transaction'}</p>
                      <p className="text-slate-500 text-xs">{new Date(tx.created_at).toLocaleString()}</p>
                    </div>
                    <div className={tx.type === 'credit' ? 'text-emerald-300' : 'text-red-300'}>
                      {tx.type === 'credit' ? '+' : '-'}₹{(tx.amount / 100).toFixed(2)}
                    </div>
                  </div>
                  <p className="mt-2 text-slate-400 text-xs">{tx.description || 'No description'}</p>
                  {tx.razorpay_payment_id ? (
                    <p className="mt-2 text-slate-500 text-xs">Payment ID: {tx.razorpay_payment_id}</p>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
