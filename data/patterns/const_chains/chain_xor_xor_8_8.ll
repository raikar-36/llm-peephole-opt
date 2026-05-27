define i32 @chain_xor_xor_8_8(i32 %x) {
entry:
  %tmp = xor i32 %x, 8
  %result = xor i32 %tmp, 8
  ret i32 %result
}
