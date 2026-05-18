<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SplitSmart</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <div class="app-shell">
        <header class="topbar">
            <div>
                <p class="eyebrow">Smart Expense Splitter</p>
                <h1>SplitSmart</h1>
                <p class="topbar-copy">Shared trips, flat bills, and dinner tabs without spreadsheet drama.</p>
            </div>
            <div class="topbar-actions card">
                <label for="current-user-select">Acting as</label>
                <select id="current-user-select"></select>
                <p id="current-user-meta" class="muted"></p>
            </div>
        </header>

        <div id="status-banner" class="status-banner hidden"></div>

        <main class="layout">
            <aside class="sidebar">
                <section class="card">
                    <div class="section-head">
                        <h2>Groups</h2>
                        <button id="refresh-groups" class="ghost-button" type="button">Refresh</button>
                    </div>
                    <div id="groups-list" class="group-list"></div>
                </section>

                <section class="card">
                    <div class="section-head">
                        <h2>Create Group</h2>
                    </div>
                    <form id="create-group-form" class="stack-form">
                        <label>
                            <span>Name</span>
                            <input name="name" type="text" placeholder="Goa Escape 2.0" required>
                        </label>
                        <label>
                            <span>Description</span>
                            <textarea name="description" rows="3" placeholder="Trip, flat, food club..."></textarea>
                        </label>
                        <fieldset class="member-picker">
                            <legend>Add members</legend>
                            <div id="group-member-options" class="pill-grid"></div>
                        </fieldset>
                        <button type="submit" class="primary-button">Create group</button>
                    </form>
                </section>

                <section class="card">
                    <div class="section-head">
                        <h2>Quick Add User</h2>
                    </div>
                    <form id="create-user-form" class="stack-form">
                        <label>
                            <span>Name</span>
                            <input name="name" type="text" placeholder="New roommate" required>
                        </label>
                        <label>
                            <span>Email</span>
                            <input name="email" type="email" placeholder="name@example.com" required>
                        </label>
                        <button type="submit" class="secondary-button">Add user</button>
                    </form>
                </section>
            </aside>

            <section class="content">
                <section id="empty-state" class="hero-card">
                    <p class="eyebrow">Ready to split</p>
                    <h2>Select a group to see balances, add expenses, and settle things cleanly.</h2>
                    <p class="muted">You already have seeded sample groups to demo the product, and you can create new ones from the sidebar.</p>
                </section>

                <section id="group-view" class="hidden">
                    <div class="hero-card">
                        <div class="hero-copy">
                            <p id="group-currency-chip" class="eyebrow"></p>
                            <h2 id="group-name"></h2>
                            <p id="group-description" class="muted"></p>
                            <div id="group-members" class="chip-row"></div>
                        </div>
                        <div class="hero-metrics">
                            <div>
                                <span class="metric-label">Expenses</span>
                                <strong id="group-expense-count"></strong>
                            </div>
                            <div>
                                <span class="metric-label">Last activity</span>
                                <strong id="group-last-activity"></strong>
                            </div>
                        </div>
                    </div>

                    <div class="stats-grid">
                        <section class="card">
                            <div class="section-head">
                                <h2>Balances</h2>
                            </div>
                            <div id="balances-list" class="stack-list"></div>
                        </section>

                        <section class="card">
                            <div class="section-head">
                                <h2>Settle Up</h2>
                            </div>
                            <div id="settlements-list" class="stack-list"></div>
                        </section>
                    </div>

                    <div class="tabs">
                        <button type="button" class="tab-button active" data-tab="manual">Manual</button>
                        <button type="button" class="tab-button" data-tab="ai-expense">AI Text</button>
                        <button type="button" class="tab-button" data-tab="bill-parser">Bill Parser</button>
                        <button type="button" class="tab-button" data-tab="history">History</button>
                    </div>

                    <section id="tab-manual" class="tab-panel active">
                        <div class="card">
                            <div class="section-head">
                                <h2>Add Expense</h2>
                                <span id="manual-source-badge" class="soft-badge">Manual</span>
                            </div>
                            <form id="expense-form" class="stack-form">
                                <div class="field-grid">
                                    <label>
                                        <span>Description</span>
                                        <input id="expense-description" name="description" type="text" placeholder="Dinner at Trupti" required>
                                    </label>
                                    <label>
                                        <span>Amount (INR)</span>
                                        <input id="expense-amount" name="amount" type="number" min="0" step="0.01" placeholder="2400.00" required>
                                    </label>
                                    <label>
                                        <span>Date</span>
                                        <input id="expense-date" name="expense_date" type="date" required>
                                    </label>
                                    <label>
                                        <span>Payer</span>
                                        <select id="expense-payer" name="payer_user_id" required></select>
                                    </label>
                                </div>

                                <label>
                                    <span>Notes</span>
                                    <textarea id="expense-notes" name="notes" rows="2" placeholder="Optional context for the group"></textarea>
                                </label>

                                <label>
                                    <span>Split mode</span>
                                    <select id="expense-split-mode" name="split_mode">
                                        <option value="equal_all">Equal among all members</option>
                                        <option value="equal_subset">Equal among a subset</option>
                                        <option value="custom">Custom amounts</option>
                                        <option value="weights">Share weights</option>
                                    </select>
                                </label>

                                <div id="bill-attachment" class="info-banner hidden"></div>
                                <div id="participant-controls" class="participant-controls"></div>
                                <div id="split-preview" class="preview-panel"></div>

                                <div class="button-row">
                                    <button type="submit" class="primary-button">Save expense</button>
                                    <button id="reset-expense-form" type="button" class="ghost-button">Reset</button>
                                </div>
                            </form>
                        </div>
                    </section>

                    <section id="tab-ai-expense" class="tab-panel">
                        <div class="card">
                            <div class="section-head">
                                <h2>Natural-Language Entry</h2>
                            </div>
                            <p class="muted">Try: “I paid 2400 for dinner last night, split between me, Aman and Priya, but Aman didn’t have drinks so reduce his share by 300.”</p>
                            <form id="ai-expense-form" class="stack-form">
                                <label>
                                    <span>Paste the expense in plain English</span>
                                    <textarea id="ai-expense-text" rows="5" placeholder="I paid 2400 for dinner last night..." required></textarea>
                                </label>
                                <button type="submit" class="secondary-button">Parse draft</button>
                            </form>
                            <div id="ai-expense-result" class="result-panel hidden"></div>
                        </div>
                    </section>

                    <section id="tab-bill-parser" class="tab-panel">
                        <div class="card">
                            <div class="section-head">
                                <h2>Bill Text Parser</h2>
                            </div>
                            <p class="muted">Paste raw bill text from a receipt. The app will extract line items, then you assign each item to people.</p>
                            <form id="bill-parser-form" class="stack-form">
                                <label>
                                    <span>Raw bill text</span>
                                    <textarea id="bill-parser-text" rows="7" placeholder="Restaurant name, items, taxes, total..." required></textarea>
                                </label>
                                <button type="submit" class="secondary-button">Parse bill</button>
                            </form>

                            <div id="bill-parser-result" class="result-panel hidden"></div>
                            <div id="bill-assignment-panel" class="hidden">
                                <div class="field-grid">
                                    <label>
                                        <span>Bill description</span>
                                        <input id="bill-draft-description" type="text">
                                    </label>
                                    <label>
                                        <span>Bill date</span>
                                        <input id="bill-draft-date" type="date">
                                    </label>
                                    <label>
                                        <span>Payer</span>
                                        <select id="bill-draft-payer"></select>
                                    </label>
                                </div>
                                <div id="bill-items-list" class="bill-items-list"></div>
                                <div id="bill-share-preview" class="preview-panel"></div>
                                <button id="use-bill-draft" type="button" class="primary-button">Use bill as expense draft</button>
                            </div>
                        </div>
                    </section>

                    <section id="tab-history" class="tab-panel">
                        <div class="card">
                            <div class="section-head">
                                <h2>Expense History</h2>
                            </div>
                            <form id="history-filter-form" class="history-filters">
                                <label>
                                    <span>Payer</span>
                                    <select id="history-payer-filter">
                                        <option value="">All payers</option>
                                    </select>
                                </label>
                                <label>
                                    <span>From</span>
                                    <input id="history-start-date" type="date">
                                </label>
                                <label>
                                    <span>To</span>
                                    <input id="history-end-date" type="date">
                                </label>
                                <label>
                                    <span>Search</span>
                                    <input id="history-search" type="text" placeholder="Dinner, rent, groceries">
                                </label>
                                <div class="button-row">
                                    <button type="submit" class="secondary-button">Apply filters</button>
                                    <button id="clear-history-filters" type="button" class="ghost-button">Clear</button>
                                </div>
                            </form>
                            <div id="history-list" class="history-list"></div>
                        </div>
                    </section>
                </section>
            </section>
        </main>
    </div>

    <script src="{{ url_for('static', filename='app.js') }}"></script>
</body>
</html>
