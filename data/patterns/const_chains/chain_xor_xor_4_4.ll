define i32 @chain_xor_xor_4_4(i32 %x) {
entry:
  %tmp = xor i32 %x, 4
  %result = xor i32 %tmp, 4
  ret i32 %result
}
