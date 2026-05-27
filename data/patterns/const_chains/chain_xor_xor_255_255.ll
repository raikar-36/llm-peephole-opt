define i32 @chain_xor_xor_255_255(i32 %x) {
entry:
  %tmp = xor i32 %x, 255
  %result = xor i32 %tmp, 255
  ret i32 %result
}
