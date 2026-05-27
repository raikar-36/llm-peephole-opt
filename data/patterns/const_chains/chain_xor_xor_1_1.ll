define i32 @chain_xor_xor_1_1(i32 %x) {
entry:
  %tmp = xor i32 %x, 1
  %result = xor i32 %tmp, 1
  ret i32 %result
}
