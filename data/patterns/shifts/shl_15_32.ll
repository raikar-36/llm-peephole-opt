define i32 @pattern_shl_15_32(i32 %x) {
entry:
  %result = shl i32 %x, 15
  ret i32 %result
}
