<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RoamBudget | Secure Trip Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
        .hidden { display: none; }
        .auth-card { animation: slideUp 0.4s ease-out; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="p-4 md:p-8">

    <div class="max-w-4xl mx-auto">
        
        <div id="auth-container" class="auth-card bg-white p-8 rounded-2xl shadow-xl border border-slate-200 max-w-md mx-auto mt-20">
            <div class="text-center mb-8">
                <h2 class="text-3xl font-bold text-indigo-600">✈️ RoamBudget</h2>
                <p class="text-slate-500 mt-2">Sign in to manage your private trip.</p>
            </div>
            
            <form id="auth-form" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-400 mb-1">Email Address</label>
                    <input type="email" id="email" placeholder="name@email.com" required class="w-full p-3 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-slate-400 mb-1">Password</label>
                    <input type="password" id="password" placeholder="••••••••" required class="w-full p-3 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
                
                <div class="flex flex-col gap-3 pt-2">
                    <button type="submit" id="btn-login" class="w-full bg-indigo-600 text-white font-bold py-3 rounded-lg hover:bg-indigo-700 transition shadow-md">
                        Login
                    </button>
                    <button type="button" id="btn-signup" class="w-full border-2 border-indigo-600 text-indigo-600 font-bold py-3 rounded-lg hover:bg-indigo-50 transition">
                        Create New Account
                    </button>
                </div>
            </form>
            <p id="auth-msg" class="text-center text-sm mt-6 text-red-500 font-medium h-4"></p>
        </div>

        <div id="app-container" class="hidden">
            <div class="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
                <div>
                    <h1 class="text-3xl font-bold text-slate-800 flex items-center gap-2">RoamBudget</h1>
                    <div class="flex items-center gap-2 mt-1">
                        <span id="user-email" class="text-sm text-slate-400 font-medium italic"></span>
                        <button id="btn-logout" class="text-xs text-red-400 hover:text-red-600 font-bold uppercase tracking-widest border-l pl-2">Sign Out</button>
                    </div>
                </div>
                <div class="bg-indigo-600 text-white p-6 rounded-2xl shadow-lg text-center min-w-[220px]">
                    <p class="text-xs uppercase tracking-widest font-semibold opacity-80">My Private Total</p>
                    <h2 id="total-cost" class="text-4xl font-bold mt-1">$0.00</h2>
                </div>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-8">
                <form id="expense-form" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="md:col-span-2">
                        <label class="block text-sm font-semibold text-slate-600 mb-1">Expense Name</label>
                        <input type="text" id="item_name" required class="w-full p-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-slate-600 mb-1">Amount ($)</label>
                        <input type="number" id="amount" step="0.01" required class="w-full p-2 border rounded-lg outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-slate-600 mb-1">Category</label>
                        <select id="category" class="w-full p-2 border rounded-lg outline-none">
                            <option value="Lodging">Lodging</option>
                            <option value="Food">Food</option>
                            <option value="Transport">Transport</option>
                            <option value="Activity">Activity</option>
                        </select>
                    </div>
                    <button type="submit" class="md:col-span-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-lg shadow-md active:scale-95 transition">
                        Add to My Trip
                    </button>
                </form>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-50 text-slate-500 text-xs uppercase font-bold border-b">
                            <th class="p-4">Item</th>
                            <th class="p-4">Category</th>
                            <th class="p-4 text-right">Cost</th>
                            <th class="p-4 text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody id="expense-table-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // --- 1. CONFIGURATION ---
        const SB_URL = "YOUR_SUPABASE_URL"; // Paste your URL here
        const SB_KEY = "YOUR_SUPABASE_ANON_KEY"; // Paste your Anon Key here
        const API_URL = "https://roambudget-server.onrender.com/expenses"; // Paste your Render link here

        // Initialize Supabase Client
        const supabaseClient = supabase.createClient(SB_URL, SB_KEY);

        // --- 2. AUTHENTICATION LOGIC ---
        async function checkUserSession() {
            const { data: { session } } = await supabaseClient.auth.getSession();
            
            if (session) {
                // User is logged in
                document.getElementById('auth-container').classList.add('hidden');
                document.getElementById('app-container').classList.remove('hidden');
                document.getElementById('user-email').innerText = session.user.email;
                fetchExpenses(session.access_token);
            } else {
                // User is logged out
                document.getElementById('auth-container').classList.remove('hidden');
                document.getElementById('app-container').classList.add('hidden');
            }
        }

        // Handle Signup
        document.getElementById('btn-signup').onclick = async () => {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const { error } = await supabaseClient.auth.signUp({ email, password });
            
            if (error) {
                document.getElementById('auth-msg').innerText = error.message;
            } else {
                alert("Success! Check your email for a confirmation link.");
            }
        };

        // Handle Login
        document.getElementById('auth-form').onsubmit = async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const { error } = await supabaseClient.auth.signInWithPassword({ email, password });
            
            if (error) {
                document.getElementById('auth-msg').innerText = "Login failed: " + error.message;
            } else {
                checkUserSession(); // This will refresh UI to the app
            }
        };

        // Handle Logout
        document.getElementById('btn-logout').onclick = async () => {
            await supabaseClient.auth.signOut();
            checkUserSession();
        };

        // --- 3. EXPENSE LOGIC ---
        async function fetchExpenses(token) {
            try {
                const response = await fetch(API_URL, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await response.json();
                renderUI(data, token);
            } catch (err) {
                console.error("API Error:", err);
            }
        }

        function renderUI(expenses, token) {
            const tableBody = document.getElementById('expense-table-body');
            const totalDisplay = document.getElementById('total-cost');
            tableBody.innerHTML = '';
            let total = 0;

            if (expenses.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="4" class="p-10 text-center text-slate-400">Empty Trip! Add something above.</td></tr>`;
                totalDisplay.innerText = "$0.00";
                return;
            }

            expenses.forEach(exp => {
                total += exp.amount;
                const row = `
                    <tr class="border-b hover:bg-slate-50 transition">
                        <td class="p-4 font-bold text-slate-700">${exp.item_name}</td>
                        <td class="p-4"><span class="px-2 py-1 text-[10px] bg-indigo-50 text-indigo-600 rounded-full font-bold uppercase">${exp.category}</span></td>
                        <td class="p-4 text-right font-bold text-slate-700">$${exp.amount.toFixed(2)}</td>
                        <td class="p-4 text-center">
                            <button onclick="deleteExp(${exp.id}, '${token}')" class="text-slate-300 hover:text-red-500 transition px-2">🗑️</button>
                        </td>
                    </tr>`;
                tableBody.insertAdjacentHTML('beforeend', row);
            });
            totalDisplay.innerText = `$${total.toFixed(2)}`;
        }

        document.getElementById('expense-form').onsubmit = async (e) => {
            e.preventDefault();
            const { data: { session } } = await supabaseClient.auth.getSession();
            
            const payload = {
                item_name: document.getElementById('item_name').value,
                amount: parseFloat(document.getElementById('amount').value),
                category: document.getElementById('category').value,
                paid_by: "Me", // Logic is now user-based
                split_count: 1
            };

            await fetch(API_URL, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify(payload)
            });

            e.target.reset();
            fetchExpenses(session.access_token);
        };

        async function deleteExp(id, token) {
            if (!confirm("Remove this?")) return;
            await fetch(`${API_URL}/${id}`, { 
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            fetchExpenses(token);
        }

        // Initialize on page load
        checkUserSession();
    </script>
</body>
</html>
