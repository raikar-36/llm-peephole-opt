define i32 @chain_xor_xor_2_2(i32 %x) {
entry:
  %tmp = xor i32 %x, 2
  %result = xor i32 %tmp, 2
  ret i32 %result
}
