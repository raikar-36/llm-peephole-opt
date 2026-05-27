define i32 @pattern_shl_1_32(i32 %x) {
entry:
  %result = shl i32 %x, 1
  ret i32 %result
}
