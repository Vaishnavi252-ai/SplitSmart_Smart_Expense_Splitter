const state = {
  users: [],
  groups: [],
  currentUserId: null,
  selectedGroupId: null,
  selectedGroup: null,
  balances: [],
  settlements: [],
  expenses: [],
  activeTab: "manual",
  historyFilters: {
    payer_user_id: "",
    start_date: "",
    end_date: "",
    search: "",
  },
  manualSourceType: "manual",
  manualAiConfidence: null,
  manualLineItems: [],
  billDraft: null,
  billAssignments: [],
};

const els = {};

document.addEventListener("DOMContentLoaded", async () => {
  cacheElements();
  bindEvents();
  setDefaultDates();
  await bootstrap();
});

function cacheElements() {
  els.banner = document.getElementById("status-banner");
  els.currentUserSelect = document.getElementById("current-user-select");
  els.currentUserMeta = document.getElementById("current-user-meta");
  els.groupsList = document.getElementById("groups-list");
  els.groupMemberOptions = document.getElementById("group-member-options");
  els.createGroupForm = document.getElementById("create-group-form");
  els.createUserForm = document.getElementById("create-user-form");
  els.emptyState = document.getElementById("empty-state");
  els.groupView = document.getElementById("group-view");
  els.groupName = document.getElementById("group-name");
  els.groupDescription = document.getElementById("group-description");
  els.groupMembers = document.getElementById("group-members");
  els.groupCurrencyChip = document.getElementById("group-currency-chip");
  els.groupExpenseCount = document.getElementById("group-expense-count");
  els.groupLastActivity = document.getElementById("group-last-activity");
  els.balancesList = document.getElementById("balances-list");
  els.settlementsList = document.getElementById("settlements-list");
  els.expenseForm = document.getElementById("expense-form");
  els.expenseDescription = document.getElementById("expense-description");
  els.expenseAmount = document.getElementById("expense-amount");
  els.expenseDate = document.getElementById("expense-date");
  els.expensePayer = document.getElementById("expense-payer");
  els.expenseNotes = document.getElementById("expense-notes");
  els.expenseSplitMode = document.getElementById("expense-split-mode");
  els.participantControls = document.getElementById("participant-controls");
  els.splitPreview = document.getElementById("split-preview");
  els.manualSourceBadge = document.getElementById("manual-source-badge");
  els.billAttachment = document.getElementById("bill-attachment");
  els.aiExpenseForm = document.getElementById("ai-expense-form");
  els.aiExpenseText = document.getElementById("ai-expense-text");
  els.aiExpenseResult = document.getElementById("ai-expense-result");
  els.billParserForm = document.getElementById("bill-parser-form");
  els.billParserText = document.getElementById("bill-parser-text");
  els.billParserResult = document.getElementById("bill-parser-result");
  els.billAssignmentPanel = document.getElementById("bill-assignment-panel");
  els.billDraftDescription = document.getElementById("bill-draft-description");
  els.billDraftDate = document.getElementById("bill-draft-date");
  els.billDraftPayer = document.getElementById("bill-draft-payer");
  els.billItemsList = document.getElementById("bill-items-list");
  els.billSharePreview = document.getElementById("bill-share-preview");
  els.useBillDraftButton = document.getElementById("use-bill-draft");
  els.historyFilterForm = document.getElementById("history-filter-form");
  els.historyPayerFilter = document.getElementById("history-payer-filter");
  els.historyStartDate = document.getElementById("history-start-date");
  els.historyEndDate = document.getElementById("history-end-date");
  els.historySearch = document.getElementById("history-search");
  els.historyList = document.getElementById("history-list");
}

function bindEvents() {
  document.getElementById("refresh-groups").addEventListener("click", refreshGroups);
  document.getElementById("reset-expense-form").addEventListener("click", resetExpenseForm);
  document.getElementById("clear-history-filters").addEventListener("click", clearHistoryFilters);

  els.currentUserSelect.addEventListener("change", async () => {
    state.currentUserId = Number(els.currentUserSelect.value);
    resetExpenseForm();
    await refreshGroups();
  });

  els.createUserForm.addEventListener("submit", createUser);
  els.createGroupForm.addEventListener("submit", createGroup);
  els.expenseForm.addEventListener("submit", saveExpense);
  els.expenseSplitMode.addEventListener("change", () => {
    if (state.manualSourceType === "ai_bill_text") {
      clearAttachedBill("Changing split mode detaches the parsed bill breakdown.");
    }
    renderParticipantControls();
  });

  els.expenseAmount.addEventListener("input", renderSplitPreview);
  els.expensePayer.addEventListener("change", renderSplitPreview);

  els.aiExpenseForm.addEventListener("submit", handleAiExpenseParse);
  els.billParserForm.addEventListener("submit", handleBillParse);
  els.useBillDraftButton.addEventListener("click", applyParsedBillDraft);
  els.historyFilterForm.addEventListener("submit", applyHistoryFilters);

  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => setActiveTab(button.dataset.tab));
  });
}

async function bootstrap() {
  try {
    await loadUsers();
    await refreshGroups();
  } catch (error) {
    showBanner(error.message || "Unable to load the app right now.", "error");
  }
}

async function loadUsers() {
  const data = await api("/api/users/");
  state.users = data.users;
  if (!state.users.length) {
    throw new Error("No users were found.");
  }

  if (!state.currentUserId || !state.users.some((user) => user.id === state.currentUserId)) {
    state.currentUserId = state.users[0].id;
  }

  renderUserSwitcher();
  renderGroupMemberOptions();
}

async function refreshGroups() {
  const userId = state.currentUserId ? `?user_id=${state.currentUserId}` : "";
  const data = await api(`/api/groups/${userId}`);
  state.groups = data.groups;
  renderGroupList();

  if (!state.groups.length) {
    state.selectedGroupId = null;
    state.selectedGroup = null;
    renderSelectedGroup();
    return;
  }

  const stillVisible = state.groups.some((group) => group.id === state.selectedGroupId);
  if (!stillVisible) {
    state.selectedGroupId = state.groups[0].id;
  }

  await loadGroup(state.selectedGroupId);
}

async function loadGroup(groupId) {
  state.selectedGroupId = groupId;
  const [group, balancesData, settlementsData, expensesData] = await Promise.all([
    api(`/api/groups/${groupId}`),
    api(`/api/groups/${groupId}/balances`),
    api(`/api/groups/${groupId}/settlements`),
    api(buildExpensesUrl(groupId)),
  ]);

  state.selectedGroup = group;
  state.balances = balancesData.balances;
  state.settlements = settlementsData.settlements;
  state.expenses = expensesData.expenses;

  renderGroupList();
  renderSelectedGroup();
}

function renderUserSwitcher() {
  els.currentUserSelect.innerHTML = state.users
    .map((user) => `<option value="${user.id}" ${user.id === state.currentUserId ? "selected" : ""}>${escapeHtml(user.name)}</option>`)
    .join("");

  const currentUser = getCurrentUser();
  els.currentUserMeta.textContent = currentUser ? currentUser.email : "";
}

function renderGroupMemberOptions() {
  els.groupMemberOptions.innerHTML = state.users
    .map((user) => {
      const checked = user.id === state.currentUserId ? "checked" : "";
      return `
        <label class="pill-option">
          <input type="checkbox" name="member_ids" value="${user.id}" ${checked}>
          <span>${escapeHtml(user.name)}</span>
        </label>
      `;
    })
    .join("");
}

function renderGroupList() {
  if (!state.groups.length) {
    els.groupsList.innerHTML = `<p class="muted">No groups for this user yet. Create one from the form below.</p>`;
    return;
  }

  els.groupsList.innerHTML = state.groups
    .map((group) => {
      const isActive = group.id === state.selectedGroupId;
      const balanceMarkup =
        typeof group.current_user_balance_paise === "number"
          ? `<p class="group-balance ${group.current_user_balance_paise > 0 ? "positive" : group.current_user_balance_paise < 0 ? "negative" : ""}">
              ${group.current_user_balance_paise > 0 ? "You get back" : group.current_user_balance_paise < 0 ? "You owe" : "All square"} 
              ${group.current_user_balance_paise === 0 ? "" : escapeHtml(group.current_user_balance_display)}
             </p>`
          : "";

      return `
        <button type="button" class="group-card ${isActive ? "active" : ""}" data-group-id="${group.id}">
          <div class="group-card-top">
            <strong>${escapeHtml(group.name)}</strong>
            <span>${group.member_count} members</span>
          </div>
          <p>${escapeHtml(group.description || "No description yet.")}</p>
          <div class="group-card-bottom">
            <span>${group.expense_count} expenses</span>
            <span>${escapeHtml(group.last_activity_label || "No activity")}</span>
          </div>
          ${balanceMarkup}
        </button>
      `;
    })
    .join("");

  els.groupsList.querySelectorAll("[data-group-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await loadGroup(Number(button.dataset.groupId));
    });
  });
}

function renderSelectedGroup() {
  const hasGroup = Boolean(state.selectedGroup);
  els.emptyState.classList.toggle("hidden", hasGroup);
  els.groupView.classList.toggle("hidden", !hasGroup);

  if (!hasGroup) {
    return;
  }

  const group = state.selectedGroup;
  els.groupName.textContent = group.name;
  els.groupDescription.textContent = group.description || "No description yet.";
  els.groupCurrencyChip.textContent = `${group.currency_code} ledger`;
  els.groupExpenseCount.textContent = String(group.expense_count);
  els.groupLastActivity.textContent = group.last_expense_date || "No expenses yet";
  els.groupMembers.innerHTML = group.members.map((member) => `<span class="chip">${escapeHtml(member.name)}</span>`).join("");

  renderBalances();
  renderSettlements();
  renderExpenseSelectors();
  renderParticipantControls();
  renderSplitPreview();
  renderHistory();
  renderBillDraftInputs();
}

function renderBalances() {
  if (!state.balances.length) {
    els.balancesList.innerHTML = `<p class="muted">No balances yet. Add the first expense to start the ledger.</p>`;
    return;
  }

  els.balancesList.innerHTML = state.balances
    .map((entry) => {
      const statusText =
        entry.status === "gets_back"
          ? `gets back ${entry.balance_display}`
          : entry.status === "owes"
            ? `owes ${entry.balance_display}`
            : `is settled up`;
      return `
        <div class="balance-row">
          <div>
            <strong>${escapeHtml(entry.name)}</strong>
            <p class="muted">${escapeHtml(entry.email)}</p>
          </div>
          <span class="balance-pill ${entry.status}">${statusText}</span>
        </div>
      `;
    })
    .join("");
}

function renderSettlements() {
  if (!state.settlements.length) {
    els.settlementsList.innerHTML = `<p class="muted">Everyone is settled. No transfers needed.</p>`;
    return;
  }

  els.settlementsList.innerHTML = state.settlements
    .map(
      (settlement) => `
        <div class="settlement-row">
          <strong>${escapeHtml(settlement.from_name)}</strong>
          <span>pays</span>
          <strong>${escapeHtml(settlement.to_name)}</strong>
          <span class="soft-badge">${escapeHtml(settlement.amount_display)}</span>
        </div>
      `
    )
    .join("");
}

function renderExpenseSelectors() {
  const members = state.selectedGroup.members;
  const payerOptions = members
    .map((member) => {
      const selected = member.id === getSuggestedPayerId() ? "selected" : "";
      return `<option value="${member.id}" ${selected}>${escapeHtml(member.name)}</option>`;
    })
    .join("");

  els.expensePayer.innerHTML = payerOptions;
  els.billDraftPayer.innerHTML = payerOptions;
  els.historyPayerFilter.innerHTML =
    `<option value="">All payers</option>` +
    members
      .map((member) => {
        const selected = String(member.id) === String(state.historyFilters.payer_user_id) ? "selected" : "";
        return `<option value="${member.id}" ${selected}>${escapeHtml(member.name)}</option>`;
      })
      .join("");

  if (!state.manualLineItems.length) {
    els.billDraftPayer.value = String(getSuggestedPayerId());
  }
}

function renderParticipantControls() {
  if (!state.selectedGroup) {
    return;
  }

  const splitMode = els.expenseSplitMode.value;
  const members = state.selectedGroup.members;
  const participantMap = getDraftParticipantMap();
  const hasDraftParticipants = participantMap.size > 0;

  let markup = "";

  if (splitMode === "equal_all") {
    markup = `<p class="muted">All ${members.length} members will share this equally.</p>`;
  } else if (splitMode === "equal_subset") {
    markup = `
      <div class="participant-grid">
        ${members
          .map((member) => {
            const participant = participantMap.get(member.id);
            const checked = participant ? participant.selected !== false : hasDraftParticipants ? false : true;
            return `
              <label class="participant-card">
                <input type="checkbox" class="participant-toggle" data-user-id="${member.id}" ${checked ? "checked" : ""}>
                <span>${escapeHtml(member.name)}</span>
              </label>
            `;
          })
          .join("")}
      </div>
    `;
  } else if (splitMode === "custom") {
    markup = `
      <div class="participant-list">
        ${members
          .map((member) => {
            const participant = participantMap.get(member.id);
            const checked = participant ? participant.selected !== false : hasDraftParticipants ? false : true;
            const value = participant && typeof participant.amount_paise === "number" ? paiseToInput(participant.amount_paise) : "";
            return `
              <div class="participant-row">
                <label class="participant-card compact">
                  <input type="checkbox" class="participant-toggle" data-user-id="${member.id}" ${checked ? "checked" : ""}>
                  <span>${escapeHtml(member.name)}</span>
                </label>
                <input type="number" min="0" step="0.01" class="participant-amount" data-user-id="${member.id}" value="${value}" placeholder="0.00">
              </div>
            `;
          })
          .join("")}
      </div>
    `;
  } else if (splitMode === "weights") {
    markup = `
      <div class="participant-list">
        ${members
          .map((member) => {
            const participant = participantMap.get(member.id);
            const checked = participant ? participant.selected !== false : hasDraftParticipants ? false : true;
            const value = participant && typeof participant.weight === "number" ? participant.weight : 1;
            return `
              <div class="participant-row">
                <label class="participant-card compact">
                  <input type="checkbox" class="participant-toggle" data-user-id="${member.id}" ${checked ? "checked" : ""}>
                  <span>${escapeHtml(member.name)}</span>
                </label>
                <input type="number" min="1" step="1" class="participant-weight" data-user-id="${member.id}" value="${value}">
              </div>
            `;
          })
          .join("")}
      </div>
    `;
  }

  els.participantControls.innerHTML = markup;

  els.participantControls.querySelectorAll("input").forEach((input) => {
    input.addEventListener("input", handleParticipantEdit);
    input.addEventListener("change", handleParticipantEdit);
  });

  renderSplitPreview();
}

function handleParticipantEdit() {
  if (state.manualSourceType === "ai_bill_text") {
    clearAttachedBill("Editing custom shares detaches the parsed bill breakdown.");
  }
  renderSplitPreview();
}

function renderSplitPreview() {
  if (!state.selectedGroup) {
    return;
  }

  const amountPaise = rupeesToPaise(els.expenseAmount.value);
  if (!amountPaise) {
    els.splitPreview.innerHTML = `<p class="muted">Enter an amount to preview how the split will land.</p>`;
    renderManualSourceBadge();
    return;
  }

  const result = computeManualShares();
  renderManualSourceBadge();

  if (!result.ok) {
    els.splitPreview.innerHTML = `<p class="error-text">${escapeHtml(result.message)}</p>`;
    return;
  }

  els.splitPreview.innerHTML = `
    <div class="section-head">
      <h3>Share preview</h3>
      <span class="soft-badge">${escapeHtml(formatPaise(amountPaise))}</span>
    </div>
    <div class="preview-grid">
      ${result.shares
        .map(
          (share) => `
            <div class="preview-item">
              <strong>${escapeHtml(share.name)}</strong>
              <span>${escapeHtml(formatPaise(share.amount_paise))}</span>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderManualSourceBadge() {
  const label =
    state.manualSourceType === "ai_natural_language"
      ? "AI draft"
      : state.manualSourceType === "ai_bill_text"
        ? "Bill draft"
        : "Manual";
  els.manualSourceBadge.textContent = label;

  if (!state.manualLineItems.length) {
    els.billAttachment.classList.add("hidden");
    els.billAttachment.innerHTML = "";
    return;
  }

  els.billAttachment.classList.remove("hidden");
  els.billAttachment.innerHTML = `
    <div>
      <strong>${state.manualLineItems.length} bill items attached</strong>
      <p class="muted">The custom split is locked to the assigned line items until you detach it.</p>
    </div>
    <button type="button" class="ghost-button" id="detach-bill-breakdown">Detach</button>
  `;

  document.getElementById("detach-bill-breakdown").addEventListener("click", () => {
    clearAttachedBill("Parsed bill breakdown removed. You can now edit the split freely.");
  });
}

async function createUser(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const payload = {
    name: String(formData.get("name") || "").trim(),
    email: String(formData.get("email") || "").trim(),
  };

  try {
    await api("/api/users/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    form.reset();
    showBanner("User added. You can include them in new groups now.", "success");
    await loadUsers();
    await refreshGroups();
  } catch (error) {
    showBanner(error.message, "error");
  }
}

async function createGroup(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const memberIds = Array.from(document.querySelectorAll('#group-member-options input[type="checkbox"]:checked')).map((input) =>
    Number(input.value)
  );

  const payload = {
    name: String(formData.get("name") || "").trim(),
    description: String(formData.get("description") || "").trim(),
    created_by_user_id: state.currentUserId,
    member_ids: memberIds,
    currency_code: "INR",
  };

  try {
    const group = await api("/api/groups/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    form.reset();
    renderGroupMemberOptions();
    showBanner("Group created.", "success");
    await refreshGroups();
    await loadGroup(group.id);
  } catch (error) {
    showBanner(error.message, "error");
  }
}

async function saveExpense(event) {
  event.preventDefault();
  if (!state.selectedGroup) {
    return;
  }

  const amountPaise = rupeesToPaise(els.expenseAmount.value);
  const preview = computeManualShares();

  if (!preview.ok) {
    showBanner(preview.message, "error");
    return;
  }

  const payload = {
    payer_user_id: Number(els.expensePayer.value),
    created_by_user_id: state.currentUserId,
    description: els.expenseDescription.value.trim(),
    amount_paise: amountPaise,
    currency_code: state.selectedGroup.currency_code,
    expense_date: els.expenseDate.value,
    split_mode: els.expenseSplitMode.value,
    participants: preview.participantsPayload,
    notes: els.expenseNotes.value.trim() || null,
    source_type: state.manualSourceType,
    ai_confidence: state.manualAiConfidence,
    line_items: state.manualLineItems,
  };

  try {
    await api(`/api/groups/${state.selectedGroupId}/expenses`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showBanner("Expense saved and balances refreshed.", "success");
    resetExpenseForm();
    await loadGroup(state.selectedGroupId);
    setActiveTab("history");
  } catch (error) {
    showBanner(error.message, "error");
  }
}

async function handleAiExpenseParse(event) {
  event.preventDefault();
  if (!state.selectedGroup) {
    showBanner("Select a group before using AI parsing.", "error");
    return;
  }

  try {
    const result = await api(`/api/groups/${state.selectedGroupId}/ai/parse-expense`, {
      method: "POST",
      body: JSON.stringify({
        text: els.aiExpenseText.value.trim(),
        current_user_id: state.currentUserId,
      }),
      allowErrorBody: true,
    });

    showAiExpenseResult(result);
    if (result.draft) {
      applyExpenseDraft(result.draft, "ai_natural_language", []);
      setActiveTab("manual");
    }

    showBanner(result.message || result.fallback_message || "AI response received.", result.success ? "success" : "warning");
  } catch (error) {
    showBanner(error.message, "error");
  }
}

async function handleBillParse(event) {
  event.preventDefault();
  if (!state.selectedGroup) {
    showBanner("Select a group before parsing a bill.", "error");
    return;
  }

  try {
    const result = await api(`/api/groups/${state.selectedGroupId}/ai/parse-bill`, {
      method: "POST",
      body: JSON.stringify({
        text: els.billParserText.value.trim(),
      }),
      allowErrorBody: true,
    });

    showBillParseResult(result);

    if (result.success && result.draft) {
      state.billDraft = result.draft;
      state.billAssignments = result.draft.line_items.map(() => state.selectedGroup.members.map((member) => member.id));
      renderBillDraftInputs();
    } else {
      state.billDraft = result.draft || null;
      state.billAssignments = [];
      renderBillDraftInputs();
    }

    showBanner(result.message || result.fallback_message || "Bill parsing finished.", result.success ? "success" : "warning");
  } catch (error) {
    showBanner(error.message, "error");
  }
}

function applyParsedBillDraft() {
  if (!state.billDraft) {
    return;
  }

  const lineItems = state.billDraft.line_items.map((item, index) => ({
    item_name: item.item_name,
    amount_paise: item.amount_paise,
    assigned_user_ids: state.billAssignments[index],
  }));

  const invalidItem = lineItems.find((item) => !item.assigned_user_ids.length);
  if (invalidItem) {
    showBanner(`Assign "${invalidItem.item_name}" to at least one member.`, "error");
    return;
  }

  const totals = computeItemAssignmentTotals(lineItems);
  const effectiveTotal = lineItems.reduce((sum, item) => sum + item.amount_paise, 0);
  const participants = Object.entries(totals).map(([userId, amountPaise]) => ({
    user_id: Number(userId),
    selected: true,
    amount_paise: amountPaise,
  }));

  applyExpenseDraft(
    {
      description: els.billDraftDescription.value.trim() || state.billDraft.description || "Parsed bill",
      amount_paise: effectiveTotal,
      currency_code: state.billDraft.currency_code || state.selectedGroup.currency_code,
      expense_date: els.billDraftDate.value || todayString(),
      payer_user_id: Number(els.billDraftPayer.value),
      split_mode: "custom",
      participants,
      warnings: state.billDraft.warnings || [],
    },
    "ai_bill_text",
    lineItems
  );

  setActiveTab("manual");
  showBanner("Bill draft moved into the expense form. Review and save it.", "success");
}

function applyExpenseDraft(draft, sourceType, lineItems) {
  state.manualSourceType = sourceType;
  state.manualAiConfidence = typeof draft.confidence === "number" ? draft.confidence : null;
  state.manualLineItems = lineItems || [];

  els.expenseDescription.value = draft.description || "";
  els.expenseAmount.value = typeof draft.amount_paise === "number" ? paiseToInput(draft.amount_paise) : "";
  els.expenseDate.value = draft.expense_date || todayString();
  if (draft.payer_user_id) {
    els.expensePayer.value = String(draft.payer_user_id);
  }
  els.expenseNotes.value = draft.notes && draft.notes.length ? draft.notes.join(" ") : "";
  if (draft.split_mode) {
    els.expenseSplitMode.value = draft.split_mode;
  }

  els.expenseForm.dataset.draftParticipants = JSON.stringify(draft.participants || []);
  renderParticipantControls();
  renderSplitPreview();
}

function resetExpenseForm() {
  els.expenseForm.reset();
  els.expenseForm.dataset.draftParticipants = "[]";
  state.manualSourceType = "manual";
  state.manualAiConfidence = null;
  state.manualLineItems = [];
  els.expenseDate.value = todayString();
  if (state.selectedGroup) {
    els.expensePayer.value = String(getSuggestedPayerId());
  }
  els.expenseSplitMode.value = "equal_all";
  renderParticipantControls();
}

function clearAttachedBill(message) {
  state.manualLineItems = [];
  if (state.manualSourceType === "ai_bill_text") {
    state.manualSourceType = "manual";
    state.manualAiConfidence = null;
  }
  renderManualSourceBadge();
  if (message) {
    showBanner(message, "warning");
  }
}

async function applyHistoryFilters(event) {
  event.preventDefault();
  state.historyFilters = {
    payer_user_id: els.historyPayerFilter.value,
    start_date: els.historyStartDate.value,
    end_date: els.historyEndDate.value,
    search: els.historySearch.value.trim(),
  };

  try {
    const data = await api(buildExpensesUrl(state.selectedGroupId));
    state.expenses = data.expenses;
    renderHistory();
  } catch (error) {
    showBanner(error.message, "error");
  }
}

async function clearHistoryFilters() {
  state.historyFilters = {
    payer_user_id: "",
    start_date: "",
    end_date: "",
    search: "",
  };
  els.historyPayerFilter.value = "";
  els.historyStartDate.value = "";
  els.historyEndDate.value = "";
  els.historySearch.value = "";

  if (state.selectedGroupId) {
    const data = await api(buildExpensesUrl(state.selectedGroupId));
    state.expenses = data.expenses;
    renderHistory();
  }
}

function renderHistory() {
  if (!state.expenses.length) {
    els.historyList.innerHTML = `<p class="muted">No expenses match these filters yet.</p>`;
    return;
  }

  els.historyList.innerHTML = state.expenses
    .map((expense) => {
      const lineItemsMarkup = expense.line_items.length
        ? `
            <div class="expense-items">
              ${expense.line_items
                .map(
                  (item) => `
                    <div class="expense-item-row">
                      <span>${escapeHtml(item.item_name)}</span>
                      <span>${escapeHtml(item.amount_display)}</span>
                    </div>
                  `
                )
                .join("")}
            </div>
          `
        : "";

      return `
        <article class="history-card">
          <div class="history-top">
            <div>
              <p class="eyebrow">${escapeHtml(expense.source_label)}</p>
              <h3>${escapeHtml(expense.description)}</h3>
            </div>
            <div class="history-amount">
              <strong>${escapeHtml(expense.amount_display)}</strong>
              <span>${escapeHtml(expense.expense_date)}</span>
            </div>
          </div>
          <p class="muted">${escapeHtml(expense.payer_name)} paid. Split: ${escapeHtml(expense.split_summary)}.</p>
          ${lineItemsMarkup}
        </article>
      `;
    })
    .join("");
}

function showAiExpenseResult(result) {
  els.aiExpenseResult.classList.remove("hidden");
  els.aiExpenseResult.innerHTML = `
    <p><strong>Confidence:</strong> ${result.draft && typeof result.draft.confidence === "number" ? Math.round(result.draft.confidence * 100) : 0}%</p>
    <p>${escapeHtml(result.message || result.fallback_message || "Draft processed.")}</p>
    ${
      result.draft && result.draft.warnings && result.draft.warnings.length
        ? `<ul class="inline-list">${result.draft.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
        : ""
    }
  `;
}

function showBillParseResult(result) {
  els.billParserResult.classList.remove("hidden");
  const draft = result.draft;
  els.billParserResult.innerHTML = `
    <p><strong>Confidence:</strong> ${draft && typeof draft.confidence === "number" ? Math.round(draft.confidence * 100) : 0}%</p>
    <p>${escapeHtml(result.message || result.fallback_message || "Bill processed.")}</p>
    ${
      draft && draft.warnings && draft.warnings.length
        ? `<ul class="inline-list">${draft.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
        : ""
    }
  `;
}

function renderBillDraftInputs() {
  const hasDraft = Boolean(state.billDraft && state.billDraft.line_items && state.billDraft.line_items.length);
  els.billAssignmentPanel.classList.toggle("hidden", !hasDraft);
  if (!hasDraft) {
    els.billItemsList.innerHTML = "";
    els.billSharePreview.innerHTML = `<p class="muted">Parsed line items will appear here.</p>`;
    return;
  }

  els.billDraftDescription.value = state.billDraft.description || state.billDraft.merchant_name || "Parsed bill";
  els.billDraftDate.value = state.billDraft.bill_date || todayString();
  els.billDraftPayer.value = String(getSuggestedPayerId());

  els.billItemsList.innerHTML = state.billDraft.line_items
    .map((item, index) => {
      const assignedIds = state.billAssignments[index] || [];
      return `
        <div class="bill-item-card">
          <div class="section-head">
            <strong>${escapeHtml(item.item_name)}</strong>
            <span class="soft-badge">${escapeHtml(formatPaise(item.amount_paise))}</span>
          </div>
          <div class="pill-grid">
            ${state.selectedGroup.members
              .map((member) => {
                const checked = assignedIds.includes(member.id) ? "checked" : "";
                return `
                  <label class="pill-option">
                    <input type="checkbox" data-item-index="${index}" data-user-id="${member.id}" class="bill-assignee" ${checked}>
                    <span>${escapeHtml(member.name)}</span>
                  </label>
                `;
              })
              .join("")}
          </div>
        </div>
      `;
    })
    .join("");

  els.billItemsList.querySelectorAll(".bill-assignee").forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      const itemIndex = Number(event.target.dataset.itemIndex);
      const userId = Number(event.target.dataset.userId);
      const assigned = new Set(state.billAssignments[itemIndex] || []);
      if (event.target.checked) {
        assigned.add(userId);
      } else {
        assigned.delete(userId);
      }
      state.billAssignments[itemIndex] = Array.from(assigned);
      renderBillSharePreview();
    });
  });

  renderBillSharePreview();
}

function renderBillSharePreview() {
  if (!state.billDraft || !state.billDraft.line_items.length) {
    return;
  }

  const lineItems = state.billDraft.line_items.map((item, index) => ({
    item_name: item.item_name,
    amount_paise: item.amount_paise,
    assigned_user_ids: state.billAssignments[index] || [],
  }));

  const invalidItem = lineItems.find((item) => !item.assigned_user_ids.length);
  if (invalidItem) {
    els.billSharePreview.innerHTML = `<p class="error-text">Assign "${escapeHtml(invalidItem.item_name)}" to at least one member.</p>`;
    return;
  }

  const totals = computeItemAssignmentTotals(lineItems);
  const previewRows = state.selectedGroup.members
    .filter((member) => totals[member.id])
    .map(
      (member) => `
        <div class="preview-item">
          <strong>${escapeHtml(member.name)}</strong>
          <span>${escapeHtml(formatPaise(totals[member.id]))}</span>
        </div>
      `
    )
    .join("");

  els.billSharePreview.innerHTML = `
    <div class="section-head">
      <h3>Item-assignment preview</h3>
      <span class="soft-badge">${escapeHtml(formatPaise(lineItems.reduce((sum, item) => sum + item.amount_paise, 0)))}</span>
    </div>
    <div class="preview-grid">${previewRows}</div>
  `;
}

function computeManualShares() {
  if (!state.selectedGroup) {
    return { ok: false, message: "Select a group first." };
  }

  const amountPaise = rupeesToPaise(els.expenseAmount.value);
  if (!amountPaise) {
    return { ok: false, message: "Enter a valid amount greater than zero." };
  }

  const splitMode = els.expenseSplitMode.value;
  const members = state.selectedGroup.members;
  let selectedMembers = [];
  let shares = [];
  let participantsPayload = [];

  if (splitMode === "equal_all") {
    shares = allocateWeighted(amountPaise, members.map((member) => ({ user_id: member.id, weight: 1, name: member.name })));
    participantsPayload = [];
  } else if (splitMode === "equal_subset") {
    selectedMembers = members.filter((member) => {
      const checkbox = els.participantControls.querySelector(`.participant-toggle[data-user-id="${member.id}"]`);
      return checkbox && checkbox.checked;
    });
    if (!selectedMembers.length) {
      return { ok: false, message: "Select at least one participant." };
    }
    shares = allocateWeighted(amountPaise, selectedMembers.map((member) => ({ user_id: member.id, weight: 1, name: member.name })));
    participantsPayload = selectedMembers.map((member) => ({ user_id: member.id, selected: true }));
  } else if (splitMode === "custom") {
    let runningTotal = 0;
    selectedMembers = [];
    participantsPayload = [];

    for (const member of members) {
      const checkbox = els.participantControls.querySelector(`.participant-toggle[data-user-id="${member.id}"]`);
      const amountInput = els.participantControls.querySelector(`.participant-amount[data-user-id="${member.id}"]`);
      if (!checkbox || !amountInput || !checkbox.checked) {
        continue;
      }
      const shareAmount = rupeesToPaise(amountInput.value);
      if (shareAmount === null) {
        return { ok: false, message: `Enter a valid amount for ${member.name}.` };
      }
      runningTotal += shareAmount;
      selectedMembers.push(member);
      participantsPayload.push({ user_id: member.id, selected: true, amount_paise: shareAmount });
      shares.push({ user_id: member.id, name: member.name, amount_paise: shareAmount });
    }

    if (!participantsPayload.length) {
      return { ok: false, message: "Select at least one participant." };
    }
    if (runningTotal !== amountPaise) {
      return { ok: false, message: `Custom split totals ${formatPaise(runningTotal)}, but the expense is ${formatPaise(amountPaise)}.` };
    }
  } else if (splitMode === "weights") {
    selectedMembers = [];
    participantsPayload = [];
    const weightedMembers = [];

    for (const member of members) {
      const checkbox = els.participantControls.querySelector(`.participant-toggle[data-user-id="${member.id}"]`);
      const weightInput = els.participantControls.querySelector(`.participant-weight[data-user-id="${member.id}"]`);
      if (!checkbox || !weightInput || !checkbox.checked) {
        continue;
      }
      const weight = Number(weightInput.value);
      if (!Number.isInteger(weight) || weight <= 0) {
        return { ok: false, message: `Weight for ${member.name} must be a positive whole number.` };
      }
      selectedMembers.push(member);
      participantsPayload.push({ user_id: member.id, selected: true, weight });
      weightedMembers.push({ user_id: member.id, weight, name: member.name });
    }

    if (!weightedMembers.length) {
      return { ok: false, message: "Select at least one participant." };
    }
    shares = allocateWeighted(amountPaise, weightedMembers);
  }

  const namedShares = shares.map((share) => ({
    user_id: share.user_id,
    name: share.name || state.selectedGroup.members.find((member) => member.id === share.user_id)?.name || "Unknown",
    amount_paise: share.amount_paise,
  }));

  return {
    ok: true,
    shares: namedShares,
    participantsPayload,
  };
}

function getDraftParticipantMap() {
  let draftParticipants = [];
  try {
    draftParticipants = JSON.parse(els.expenseForm.dataset.draftParticipants || "[]");
  } catch (_error) {
    draftParticipants = [];
  }
  return new Map(draftParticipants.filter((participant) => participant.user_id).map((participant) => [participant.user_id, participant]));
}

function setActiveTab(tabName) {
  state.activeTab = tabName;
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  });
}

function getSuggestedPayerId() {
  if (state.selectedGroup && state.selectedGroup.members.some((member) => member.id === state.currentUserId)) {
    return state.currentUserId;
  }
  return state.selectedGroup?.members?.[0]?.id || state.currentUserId;
}

function buildExpensesUrl(groupId) {
  const params = new URLSearchParams();
  Object.entries(state.historyFilters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  const queryString = params.toString();
  return `/api/groups/${groupId}/expenses${queryString ? `?${queryString}` : ""}`;
}

function allocateWeighted(totalPaise, entries) {
  const totalWeight = entries.reduce((sum, entry) => sum + entry.weight, 0);
  const baseEntries = entries.map((entry, index) => {
    const numerator = totalPaise * entry.weight;
    return {
      ...entry,
      index,
      amount_paise: Math.floor(numerator / totalWeight),
      remainder_rank: numerator % totalWeight,
    };
  });

  let allocated = baseEntries.reduce((sum, entry) => sum + entry.amount_paise, 0);
  let remainder = totalPaise - allocated;
  baseEntries
    .slice()
    .sort((left, right) => right.remainder_rank - left.remainder_rank || left.index - right.index)
    .forEach((entry) => {
      if (remainder > 0) {
        entry.amount_paise += 1;
        remainder -= 1;
      }
    });

  return baseEntries;
}

function computeItemAssignmentTotals(lineItems) {
  const totals = {};
  lineItems.forEach((item) => {
    const shares = allocateWeighted(
      item.amount_paise,
      item.assigned_user_ids.map((userId) => ({ user_id: userId, weight: 1 }))
    );
    shares.forEach((share) => {
      totals[share.user_id] = (totals[share.user_id] || 0) + share.amount_paise;
    });
  });
  return totals;
}

function getCurrentUser() {
  return state.users.find((user) => user.id === state.currentUserId) || null;
}

function setDefaultDates() {
  els.expenseDate.value = todayString();
}

function showBanner(message, tone = "info") {
  if (!message) {
    els.banner.classList.add("hidden");
    els.banner.textContent = "";
    return;
  }
  els.banner.textContent = message;
  els.banner.className = `status-banner ${tone}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
    },
    body: options.body,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (options.allowErrorBody && data) {
      return data;
    }
    const details = Array.isArray(data.details) ? data.details.map((entry) => entry.msg).join(" ") : "";
    throw new Error(data.error || details || "Request failed.");
  }
  return data;
}

function rupeesToPaise(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) {
    return null;
  }
  return Math.round(number * 100);
}

function paiseToInput(value) {
  return (value / 100).toFixed(2);
}

function formatPaise(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value / 100);
}

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
