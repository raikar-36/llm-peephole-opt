define i32 @chain_add_sub_1_1(i32 %x) {
entry:
  %tmp = add i32 %x, 1
  %result = sub i32 %tmp, 1
  ret i32 %result
}
