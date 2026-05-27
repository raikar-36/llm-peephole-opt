define i32 @chain_xor_xor_16_16(i32 %x) {
entry:
  %tmp = xor i32 %x, 16
  %result = xor i32 %tmp, 16
  ret i32 %result
}
