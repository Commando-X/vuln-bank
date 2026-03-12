# Beneficiary GraphQL Endpoints (Intentionally Vulnerable)

Endpoint: `/graphql/beneficiaries`

Supported operations:
- `beneficiaries(userId: Int)`
- `beneficiary(id: Int)`
- `nameEnquiry(accountNumber: String)`
- `addBeneficiary(input: BeneficiaryInput)`
- `updateBeneficiary(id: Int, input: BeneficiaryUpdateInput)`
- `deleteBeneficiary(id: Int)`
- `verifyBeneficiary(id: Int, autoVerify: Boolean)`
- `verifyBeneficiaryOtp(id: Int, otp: String)`

Notes:
- This endpoint is intentionally vulnerable for security testing.
- Introspection, verbose error messages, and batch queries are enabled.

---

Endpoint: `/graphql/wallets`

Supported operations:
- `wallets(userId: Int)`
- `exchangeRates`
- `createWallet(input: WalletCreateInput)`
- `switchWallet(input: WalletSwitchInput)`
- `convertMainToWallet(input: WalletConversionInput)`
- `internalWalletTransfer(input: WalletTransferInput)`
- `transferToWallet(input: WalletP2PTransferInput)`
- `fundVirtualCard(input: WalletCardFundingInput)`
- `updateExchangeRate(input: ExchangeRateInput)` (admin intent, bypass bug included)

Notes:
- Default account-creation wallet is USD.
- Additional wallets can be created from the dashboard wallet UI.
