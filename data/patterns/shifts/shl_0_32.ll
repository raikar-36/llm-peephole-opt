define i32 @pattern_shl_0_32(i32 %x) {
entry:
  %result = shl i32 %x, 0
  ret i32 %result
}
