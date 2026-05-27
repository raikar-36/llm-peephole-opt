define i32 @chain_or_or_16_16(i32 %x) {
entry:
  %tmp = or i32 %x, 16
  %result = or i32 %tmp, 16
  ret i32 %result
}
