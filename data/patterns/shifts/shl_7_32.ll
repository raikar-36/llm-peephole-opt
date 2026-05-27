define i32 @pattern_shl_7_32(i32 %x) {
entry:
  %result = shl i32 %x, 7
  ret i32 %result
}
