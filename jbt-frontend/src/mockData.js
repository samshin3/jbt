export const mockGroups = [
  {
    group_id: 1,
    group_name: "Japan Trip 2026",
    location: "Japan",
    start_date: "2026-04-29",
    end_date: "2026-05-09",
    status_flag: "active",
    description: "Our Japan trip funds tracker",
    created_by: "Sam",
    image: "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=200&h=200&fit=crop"
  },
  {
    group_id: 2,
    group_name: "Boba Group Chat",
    location: "Toronto",
    start_date: "2026-01-01",
    end_date: "2026-12-31",
    status_flag: "active",
    description: "Boba runs",
    created_by: "Michelle",
    image: null
  },
  {
    group_id: 3,
    group_name: "Manulife Co-ops",
    location: "Waterloo",
    start_date: "2025-09-01",
    end_date: "2025-12-31",
    status_flag: "inactive",
    description: "Co-op expenses",
    created_by: "Sam",
    image: null
  },
]

export const mockMembers = {
  1: [
    { username: "Sam", email: "sam@email.com", is_owner: true },
    { username: "Michelle", email: "michelle@email.com", is_owner: false },
    { username: "Joanna", email: "joanna@email.com", is_owner: false },
    { username: "Tristan", email: "tristan@email.com", is_owner: false },
  ],
  2: [
    { username: "Sam", email: "sam@email.com", is_owner: false },
    { username: "Michelle", email: "michelle@email.com", is_owner: true },
  ],
  3: [
    { username: "Sam", email: "sam@email.com", is_owner: true },
    { username: "Joanna", email: "joanna@email.com", is_owner: false },
  ],
}

export const mockTransactions = {
  1: [
    { event_id: 1, event_name: "Dinner", date: "2026-04-29", total: 300, paid_by: "Sam" },
    { event_id: 2, event_name: "Lunch", date: "2026-04-29", total: 100, paid_by: "Sam" },
    { event_id: 3, event_name: "Donquiote", date: "2026-04-29", total: 67, paid_by: "Tristan" },
    { event_id: 4, event_name: "Gift shop", date: "2026-04-29", total: 90, paid_by: "Joanna" },
    { event_id: 5, event_name: "Shinkansen", date: "2026-04-29", total: 1000, paid_by: "Michelle" },
    { event_id: 6, event_name: "GU Shopping spree", date: "2026-04-29", total: 900, paid_by: "Michelle" },
    { event_id: 7, event_name: "7-Eleven", date: "2026-04-29", total: 20, paid_by: "Sam" },
  ],
  2: [],
  3: [],
}

export const mockBalances = {
  1: {
    Sam: { Michelle: 300, Joanna: 102, Tristan: -200 },
    Michelle: { Sam: -300, Joanna: 50, Tristan: 100 },
    Joanna: { Sam: -102, Michelle: -50, Tristan: 80 },
    Tristan: { Sam: 200, Michelle: -100, Joanna: -80 },
  }
}
